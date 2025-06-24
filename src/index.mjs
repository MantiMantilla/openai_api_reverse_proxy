// index.mjs

import https from 'https';

// Your secret API key for your reverse proxy
const REVERSE_PROXY_API_KEY = process.env.REVERSE_PROXY_API_KEY;

// Your OpenAI API Key
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;

// OpenAI API endpoint
const OPENAI_HOST = 'api.openai.com';
const OPENAI_PATH_PREFIX = '/v1/';

export const handler = awslambda.streamifyResponse(async (event, responseStream) => {
    console.log('Received event:', JSON.stringify(event, null, 2));

    // 1. API Key Validation
    const clientApiKey = event.headers['x-api-key'] || event.queryStringParameters?.['api_key'];

    if (!clientApiKey || clientApiKey !== REVERSE_PROXY_API_KEY) {
        // Correct way to set headers for a non-streaming error response with streamifyResponse
        const metadata = {
            statusCode: 401,
            headers: {
                'Content-Type': 'application/json',
            },
        };
        const errorResponseStream = awslambda.HttpResponseStream.from(responseStream, metadata);
        errorResponseStream.write(JSON.stringify({ error: 'Unauthorized: Invalid API Key' }));
        errorResponseStream.end(); // Important to end the stream
        console.error('Unauthorized access: Invalid API key.');
        return;
    }

    // Determine the OpenAI endpoint based on the incoming request path
    const openAIEndpoint = event.rawPath.startsWith('/')
        ? OPENAI_PATH_PREFIX + event.rawPath.substring(1)
        : OPENAI_PATH_PREFIX + event.rawPath;

    // Prepare headers for the OpenAI request
    const openAIHeaders = {
        'Content-Type': event.headers['content-type'] || 'application/json',
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Connection': 'keep-alive', // Important for streaming
    };

    // Remove any headers that might interfere or are specific to your proxy
    delete openAIHeaders['x-api-key'];
    delete openAIHeaders['host'];
    delete openAIHeaders['user-agent']; // OpenAI might not like this from Lambda

    const requestBody = event.body ? Buffer.from(event.body, event.isBase64Encoded ? 'base64' : 'utf8') : null;

    const options = {
        hostname: OPENAI_HOST,
        path: openAIEndpoint,
        method: event.requestContext.http.method,
        headers: openAIHeaders,
    };

    console.log('Forwarding request to OpenAI:', options);

    try {
        const openaiReq = https.request(options, (openaiRes) => {
            console.log('OpenAI response status:', openaiRes.statusCode);
            console.log('OpenAI response headers:', openaiRes.headers);

            // --- THIS IS THE KEY CHANGE ---
            // Create a new stream that includes the response metadata (status code and headers)
            const responseMetadata = {
                statusCode: openaiRes.statusCode,
                headers: openaiRes.headers,
            };
            const streamingResponse = awslambda.HttpResponseStream.from(responseStream, responseMetadata);

            // Pipe the OpenAI response stream directly to the new streamingResponse object
            openaiRes.pipe(streamingResponse);

            openaiRes.on('end', () => {
                console.log('OpenAI response stream ended.');
                // streamingResponse.end() is automatically called by pipe when openaiRes ends
            });

            openaiRes.on('error', (err) => {
                console.error('Error from OpenAI response stream:', err);
                // Handle errors that occur *during* streaming
                // If the stream is already open, writing an error here might cause issues
                // A robust solution would involve signaling stream error to client (e.g. malformed SSE)
                // For now, if stream is open, it might just break.
                // If it's a very early error before stream really starts, this might work.
                streamingResponse.write(JSON.stringify({ error: 'Error streaming from OpenAI', details: err.message }));
                streamingResponse.end();
            });
        });

        openaiReq.on('error', (err) => {
            console.error('Error making request to OpenAI:', err);
            // This error happens before any streaming starts, so we can send a proper error response
            const metadata = {
                statusCode: 500,
                headers: { 'Content-Type': 'application/json' },
            };
            const errorResponseStream = awslambda.HttpResponseStream.from(responseStream, metadata);
            errorResponseStream.write(JSON.stringify({ error: 'Failed to connect to OpenAI', details: err.message }));
            errorResponseStream.end();
        });

        if (requestBody) {
            openaiReq.write(requestBody);
        }
        openaiReq.end();

    } catch (error) {
        console.error('Caught an unexpected error:', error);
        // This is a catch-all for synchronous errors in your handler logic
        const metadata = {
            statusCode: 500,
            headers: { 'Content-Type': 'application/json' },
        };
        const errorResponseStream = awslambda.HttpResponseStream.from(responseStream, metadata);
        errorResponseStream.write(JSON.stringify({ error: 'Internal Server Error', details: error.message }));
        errorResponseStream.end();
    }
});

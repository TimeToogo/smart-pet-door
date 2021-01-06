from config import Config

from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

@app.get("/api/test")
async def test_api():
    return {"message": "Hello World"}

app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")

# Safari on iOS/Mac require servers to respect range headers for video
# Additionally videos must be transcoded with the "-movflags +faststart" ffmpeg flag
@app.middleware("http")
async def fulfil_http_range_header(request: Request, call_next):
    response = await call_next(request)

    if 'range' in request.headers and isinstance(response, StreamingResponse):

        content_length = int(response.headers.get('content-length'))

        content_range = request.headers.get('range').strip().lower()
        content_ranges = content_range.split('=')[-1]
        range_start, range_end, *_ = map(str.strip, (content_ranges + '-').split('-'))

        range_start = max(0, int(range_start)) if range_start else 0
        range_end   = min(content_length - 1, int(range_end)) if range_end else content_length - 1

        response.body_iterator = yield_byte_range(response, response.body_iterator, range_start, range_end)
        response.headers['content-range'] = f'bytes {range_start}-{range_end}/{content_length - 1}'
        response.headers['content-length'] = str(range_end - range_start + 1)
        response.headers['Accept-Range'] = 'bytes'
        response.status_code = 206

    return response

async def yield_byte_range(response, inner_gen, offset_start, offset_end):
    curr_offset = 0
    async for chunk in inner_gen:
        if not isinstance(chunk, bytes):
            chunk = chunk.encode(response.charset)
        
        relative_offset_start = offset_start - curr_offset
        relative_offset_end = offset_end - curr_offset

        # check if not at offset yet
        if len(chunk) < relative_offset_start:
            curr_offset += len(chunk)
            continue
        
        # finish if finished range
        if relative_offset_end < 0:
            break

        start_i = max(relative_offset_start, 0)
        end_i = min(relative_offset_end + 1, len(chunk))

        yield chunk[start_i:end_i]

        curr_offset += len(chunk)

def api():
    import asyncio
    from hypercorn.config import Config as HypConfig
    from hypercorn.asyncio import serve

    hyp_config = HypConfig()
    hyp_config.bind = [Config.API_BIND]

    asyncio.run(serve(app, hyp_config))

if __name__ == '__main__':
    api()
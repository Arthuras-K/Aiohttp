from aiohttp import web
from models import engine, Session, BaseModel
from views import AnnouncementView


app = web.Application()

async def orm_context(app: web.Application):
    print('START')
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
        await conn.run_sync(BaseModel.metadata.create_all)        
    yield
    await engine.dispose()
    print('SHUTDOWN')

@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request['session'] = session
        return await handler(request)

app.cleanup_ctx.append(orm_context)
app.middlewares.append(session_middleware)

app.add_routes([
    web.get('/announcements/{announcement_id:\d+}', AnnouncementView),
    web.post('/announcements/', AnnouncementView),
    web.patch('/announcements/{announcement_id:\d+}', AnnouncementView),
    web.delete('/announcements/{announcement_id:\d+}', AnnouncementView),
])

if __name__ == '__main__':
    web.run_app(app)
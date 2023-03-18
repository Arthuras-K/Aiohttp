import json
from bcrypt import hashpw, gensalt, checkpw
from sqlalchemy.exc import IntegrityError
from aiohttp import web
from models import Announcement, engine, Session, BaseModel


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

async def get_user(user_id: int, session: Session):
    user = await session.get(Announcement, user_id)
    if user is None:
        raise web.HTTPNotFound(text=json.dumps({'status': 'error', 'message': 'user not faund'}),
        content_type='application/json')
    
    return user

def hash_password(password:str):
    password = password.encode()
    password = hashpw(password, salt=gensalt())
    return password.decode()

class UserView(web.View):
    async def get(self):
        session = self.request["session"]
        user_id = int(self.request.match_info['user_id'])
        user = await get_user(user_id, session)
        return web.json_response({
            'id': user.id,
            'name': user.username,
            'creation_time': user.creation_time.isoformat()
        })

    async def post(self):
        session = self.request['session']
        json_data = await self.request.json()
        json_data['password'] = hash_password(json_data['password'])
        user = Announcement(**json_data)
        session.add(user)
        try:
            await session.commit()
        except IntegrityError as er:
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'user already exists'}),
        content_type='application/json')
        
        return web.json_response({
            'id':user.id
        })

    async def patch(self):
        user_id = int(self.request.match_info['user_id'])
        user = await get_user(user_id, self.request['session'])
        json_data = await self.request.json()
        if 'password' in json_data:
            json_data['password'] = hash_password(json_data['password'])
        for field, value in json_data.items():
            setattr(user, field, value)
        self.request['session'].add(user)
        await self.request['session'].commit()
        return web.json_response({'status': 'success'})


    async def delete(self):
        user_id = int(self.request.match_info['user_id'])
        user = await get_user(user_id, self.request['session'])   
        await self.request['session'].delete(user)
        await self.request['session'].commit()
        return web.json_response({'status': 'success'})


app.add_routes([
    web.get('/users/{user_id:\d+}', UserView),
    web.post('/users/', UserView),
    web.patch('/users/{user_id:\d+}', UserView),
    web.delete('/users/{user_id:\d+}', UserView),
])

if __name__ == '__main__':
    web.run_app(app)
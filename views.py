import json
from sqlalchemy.exc import IntegrityError
from aiohttp import web
from models import Announcement, Session
from auth import hash_password, check_password


async def get_announcement(announcement_id: int, session: Session):
    announcement = await session.get(Announcement, announcement_id)
    if announcement is None:
        raise web.HTTPNotFound(text=json.dumps({'status': 'error', 'message': 'announcement not faund'}),
        content_type='application/json')
    
    return announcement



class AnnouncementView(web.View):

    async def get(self):
        session = self.request["session"]
        announcement_id = int(self.request.match_info['announcement_id'])
        announcement = await get_announcement(announcement_id, session)
        return web.json_response({
            'id': announcement.id,
            'owner': announcement.owner,
            'creation_time': announcement.creation_time.isoformat(),
            'title': announcement.title,
            'descriptione': announcement.descriptione,
            })

    async def post(self):
        session = self.request['session']
        json_data = await self.request.json()
        json_data['password'] = hash_password(json_data['password'])
        announcement = Announcement(**json_data)
        session.add(announcement)
        try:
            await session.commit()
        except IntegrityError as er:
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'announcement already exists'}),
            content_type='application/json')
        return web.json_response({'status': 'success, announcement created'})

    async def patch(self):
        announcement_id = int(self.request.match_info['announcement_id'])
        announcement = await get_announcement(announcement_id, self.request['session'])
        json_data = await self.request.json()
        if 'owner' not in json_data  or 'password' not in json_data:
            raise web.HTTPConflict(text=json.dumps({'status': 'error', 'message': 'miss login or password'}),
            content_type='application/json')

        if json_data['owner'] != announcement.owner or not check_password(json_data['password'], announcement.password):
            raise web.HTTPUnauthorized(text=json.dumps({'status': 'error', 'message': 'incorrect login or password'}),
            content_type='application/json')

        json_data['password'] = hash_password(json_data['password'])
        for field, value in json_data.items():
            setattr(announcement, field, value)
        self.request['session'].add(announcement)
        await self.request['session'].commit()

        return web.json_response({'status': 'success, announcement patched'})

    async def delete(self):
        announcement_id = int(self.request.match_info['announcement_id'])
        announcement = await get_announcement(announcement_id, self.request['session'])   
        await self.request['session'].delete(announcement)
        await self.request['session'].commit()
        return web.json_response({'status': 'success, announcement deleted'})



    def raise_http_error(error_class, message: str | dict):
        raise error_class(
            text=json.dumps({"status": "error", "description": message}),
            content_type="application/json",
        )
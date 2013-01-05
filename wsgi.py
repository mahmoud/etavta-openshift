from __future__ import unicode_literals

import os
from pprint import pformat

from werkzeug.exceptions import NotFound
from werkzeug.wsgi import SharedDataMiddleware
from clastic import Application
from clastic.render.mako_templates import MakoRenderFactory

from schedule import Schedule, fm

from tzone import Pacific
import datetime


def get_pacific_time(dt=None):
    dt = dt or datetime.datetime.now(Pacific)
    try:
        ret = dt.astimezone(Pacific)
    except ValueError:
        ret = dt.replace(tzinfo=Pacific)
    return ret


def home(schedule):
    return {'content': pformat([s for s in schedule.stations])}


def get_stops(schedule, name_index, station_name, start_time=None):
    start_time = get_pacific_time(start_time)
    station_name = name_index[station_name]
    stops = schedule.get_stops(station_name, start_time)
    content = pformat(stops)
    return {'content': content}


def not_found(*a, **kw):
    raise NotFound()


def create_app(schedule_dir, template_dir, with_static=True):
    schedule = Schedule.from_directory(schedule_dir)
    resources = {'schedule': schedule,
                 'name_index': fm}
    subroutes = [('/', home, 'base.html'),
                 ('/<path:station_name>', get_stops, 'base.html'),
                 ('/favicon.ico', not_found)]
    mako_response = MakoRenderFactory(template_dir)
    subapp = Application(subroutes, resources, mako_response)

    routes = [('/', subapp), ('/v2/', subapp)]
    app = Application(routes)
    if with_static:
        app.__call__ = SharedDataMiddleware(app.__call__, {
            '/static':  os.path.join(os.path.dirname(__file__), 'static')
        })
    return app


application = create_app('raw_schedules', './templates')


if __name__ == '__main__':
    application.serve()

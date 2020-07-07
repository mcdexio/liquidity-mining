
import argparse
import json
from sqlalchemy.ext.declarative import DeclarativeMeta

from api import get_user_rewards, get_watchers

class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)     # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                        fields[field] = None
            # a json-encodable dict
            return fields
        return json.JSONEncoder.default(self, obj)

def main():
    parser = argparse.ArgumentParser(
        description='MCDEX Liquidity Mining Tool')

    subparsers = parser.add_subparsers(help="commands")

    watcher_parser = subparsers.add_parser('watcher', help="show watcher status")
    watcher_parser.set_defaults(which='watcher')
    reward_parser = subparsers.add_parser('reward', help="query mining rewards")

    reward_parser.add_argument('address', metavar='ADDRESS', action='store', type=str,
                               help='the holder\'s address to query')
    reward_parser.set_defaults(which='reward')

    parser.set_defaults(which='nothing')

    args = parser.parse_args()
    
    if args.which == 'watcher':
        watchers = get_watchers()
        print(json.dumps(watchers, cls=AlchemyEncoder, indent=4))
    elif args.which == 'reward':
        rewards = get_user_rewards(args.address)
        print(json.dumps(rewards, indent=4))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

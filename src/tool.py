
import argparse
import json
from api import get_user_rewards, get_watchers


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
        print(json.dumps(watchers, indent=4))
    elif args.which == 'reward':
        rewards = get_user_rewards(args.address)
        print(json.dumps(rewards, indent=4))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

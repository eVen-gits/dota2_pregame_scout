import os
from os import path
import re
import sys
import time
import json
import requests
from ratelimit import limits, sleep_and_retry

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import argparse
from tqdm import tqdm
from datetime import datetime, timedelta

#TODO:
#Moving average
#Regions
#Time heatmaps
#Last LPQ game
#Slot analysis - where people put items

#public enum MatchLaneType : int
#    {
#        Unknown = -1,
#        Roaming = 0,
#        SafeLane,
#        MidLane,
#        OffLane,
#        Jungle
#    }

#0 = Core, 1 = Light Support, 2 = Hard Support, also.

class Config:
    def __init__(self):
        pass

hero_alert = [
    1,	#Anti-Mage
    #2,	#Axe
    #3,	#Bane
    #4,	#Bloodseeker
    #5,	#Crystal Maiden
    #6,	#Drow Ranger
    #7,	#Earthshaker
    #8,	#Juggernaut
    #9,	#Mirana
    10,	#Morphling
    #11,	#Shadow Fiend
    #12,	#Phantom Lancer
    #13,	#Puck
    #14,	#Pudge
    #15,	#Razor
    #16,	#Sand King
    17,	#Storm Spirit
    #18,	#Sven
    #19,	#Tiny
    #20,	#Vengeful Spirit
    #21,	#Windranger
    #22,	#Zeus
    23,	#Kunkka
    #25,	#Lina
    #26,	#Lion
    #27,	#Shadow Shaman
    #28,	#Slardar
    #29,	#Tidehunter
    #30,	#Witch Doctor
    #31,	#Lich
    32,	#Riki
    33,	#Enigma
    34,	#Tinker
    #35,	#Sniper
    #36,	#Necrophos
    #37,	#Warlock
    #38,	#Beastmaster
    #39,	#Queen of Pain
    #40,	#Venomancer
    #41,	#Faceless Void
    #42,	#Wraith King
    #43,	#Death Prophet
    #44,	#Phantom Assassin
    #45,	#Pugna
    46,	#Templar Assassin
    #47,	#Viper
    #48,	#Luna
    #49,	#Dragon Knight
    #50,	#Dazzle
    #51,	#Clockwerk
    #52,	#Leshrac
    53,	#Nature's Prophet
    #54,	#Lifestealer
    #55,	#Dark Seer
    56,	#Clinkz
    #57,	#Omniknight
    #58,	#Enchantress
    59,	#Huskar
    #60,	#Night Stalker
    61,	#Broodmother
    #62,	#Bounty Hunter
    #63,	#Weaver
    #64,	#Jakiro
    #65,	#Batrider
    66,	#Chen
    #67,	#Spectre
    #68,	#Ancient Apparition
    #69,	#Doom
    70,	#Ursa
    #71,	#Spirit Breaker
    #72,	#Gyrocopter
    73,	#Alchemist
    #74,	#Invoker
    #75,	#Silencer
    #76,	#Outworld Devourer
    #77,	#Lycan
    #78,	#Brewmaster
    #79,	#Shadow Demon
    80,	#Lone Druid
    #81,	#Chaos Knight
    82,	#Meepo
    #83,	#Treant Protector
    #84,	#Ogre Magi
    #85,	#Undying
    #86,	#Rubick
    #87,	#Disruptor
    #88,	#Nyx Assassin
    #89,	#Naga Siren
    #90,	#Keeper of the Light
    91,	#Io
    92,	#Visage
    #93,	#Slark
    #94,	#Medusa
    #95,	#Troll Warlord
    #96,	#Centaur Warrunner
    #97,	#Magnus
    98,	#Timbersaw
    #99,	#Bristleback
    #100,	#Tusk
    101,	#Skywrath Mage
    #102,	#Abaddon
    #103,	#Elder Titan
    #104,	#Legion Commander
    105,	#Techies
    #106,	#Ember Spirit
    #107,	#Earth Spirit
    #108,	#Underlord
    109,	#Terrorblade
    #110,	#Phoenix
    111,	#Oracle
    #112,	#Winter Wyvern
    113,	#Arc Warden
    114,	#Monkey King
    #119,	#Dark Willow
    120,	#Pangolier
    #121,	#Grimstroke
]
hero_alert_threshold = 5

match_filter= {
    'lobbyType':7,
    'isParty':False,
    'take':250,
    #'startDateTime':int(time.mktime((datetime.today() - timedelta(days=90)).timetuple()))
}

def timeit(method):
    def timed(*args, **kw):
        sys.stdout.write('\rt({}) ...'.format(method.__name__))
        sys.stdout.flush()

        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            #print('%r  %2.2f ms' % (method.__name__, (te - ts) * 1000))
            sys.stdout.write('\rt({}) = {:.2f} ms\n'.format(method.__name__, (te - ts) * 1000))
            sys.stdout.flush()
        return result
    return timed

@sleep_and_retry
@limits(calls=50, period=36)
def call_api(url):
    response = client.get(url)
    if response.status_code != 200:
        raise Exception('API response: {}'.format(response.status_code))
    return response

def parse_server_log(file):
    games = list()
    with open(file) as f:
        #\\d:\\[\\w:\\d:(\\d*)*]
        lines = f.readlines()
        for line in lines:
            lobby = re.findall(r'\(Lobby([^\)]+)\)', line)
            if lobby:
                players = re.findall(r'\d+:\[[A-Z]:\d:\d*]', lobby[0])
                players = [re.findall(r'\d+', p)[-1] for p in players]
                games.append(players)
                #print('___________\n\t{}\n\tFound {} players:\n\t\t{}\n\t___________'.format(
                #    '\n\t'.join(line.split('(')),
                #    len(players),
                #    '\n\t\t'.join(players)
                #    ))
    return games

class Object(object):
    pass

class Json2Obj:
    def __init__(self, data):
        self.__dict__ = data
        for i in self.__dict__.keys():
            child = self.__dict__[i]
            if isinstance(child, dict):
                if len(child) > 0:
                    self.__dict__[i] = Json2Obj(child)
            if isinstance(child, list):
                self.__dict__[i] = []
                for item in child:
                    if isinstance(item, dict):
                        self.__dict__[i].append(Json2Obj(item))
                    else:
                        self.__dict__[i].append(item)

class FileModifiedHandler(FileSystemEventHandler):

    def __init__(self, path, file_name, callback):
        self.path = path
        self.file_name = file_name
        self.callback = callback

        # set observer to watch for changes in the directory
        self.observer = Observer()
        self.observer.schedule(self, path, recursive=False)
        self.observer.start()
        self.observer.join()

    def on_modified(self, event, *nargs, **kwargs):
        # only act on the change that we're looking for
        if not event.is_directory and event.src_path.endswith(self.file_name):
            self.observer.stop() # stop watching
            return self.callback(os.path.join(self.path, self.file_name)) # call callback

class Player(Json2Obj):
    def __init__(self, steamid, **kwargs):
        url = "https://api.stratz.com/api/v1/Player/{}"
        Json2Obj.__init__(self,
            json.loads(
                call_api(
                    url.format(steamid)
                ).text
            ))

        self._fishyPlayerIndicators = None
        self._heroAlert = None

        self.setup(**kwargs)

    def setup(self, **kwargs):
        url = 'https://api.stratz.com/api/v1/Player/{}/behaviorChart?'
        for key, value in kwargs.items():
            url += '&{}={}'.format(key, value)

        self.behavior = Json2Obj(
            json.loads(
                call_api(
                    url.format(self.steamId)
                ).text
            )
        )

        for hero in self.behavior.heroes:
            if not hasattr(hero, 'winCount'):
                hero.winCount = 0
            if not hasattr(hero, 'lossCount'):
                hero.lossCount = 0
            hero.winrate = hero.winCount/hero.matchCount
            hero.heroInfo = getattr(heroes, str(hero.heroId))
            hero.score = hero.winrate * hero.avgImp/100

        if not hasattr(self, 'rank'):
            self.rank = None
        if not hasattr(self, 'leaderBoardRank'):
            self.leaderBoardRank = None

        self.behavior.heroes = sorted(self.behavior.heroes, key=lambda x: (x.score), reverse=True)
        if self.behavior.matchCount == 0:
            self.behavior.winrate = 0
        else:
            self.behavior.winrate = self.behavior.winCount/self.behavior.matchCount

        if self.matchCount == 0:
            self.winrate = 0
        else:
            self.winrate = self.winCount/self.matchCount

        self.firstMatchDate = datetime.fromtimestamp(self.firstMatchDate)

    @property
    def fishyPlayerIndicators(self):
        if not self._fishyPlayerIndicators:
            info = Object()
            setattr(info, 'matchCount', self.matchCount < 750)
            setattr(info, 'isAnonymous', self.isAnonymous)
            setattr(info, 'isStratzAnonymous', self.isStratzAnonymous)
            setattr(info, 'accountAge', (datetime.now() -self.firstMatchDate).days < 365)
            setattr(info, 'winrate', self.winrate > 0.6)
            setattr(info, 'winrate', self.behavior.winrate > 0.7)
            setattr(info, 'flagsSum', sum(info.__dict__.values()))
            self._fishyPlayerIndicators = info
        return self._fishyPlayerIndicators

    @property
    def heroAlert(self):
        if self._heroAlert == None:
            self._heroAlert = list()
            for hero in self.behavior.heroes:
                if hero.heroId in hero_alert and hero.matchCount >= hero_alert_threshold:
                    self._heroAlert.append(hero)
                    #print('\t{}: {} {:.0%}'.format(hero.heroInfo.displayName, hero.matchCount, hero.winrate))
        return self._heroAlert

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""""")

    if os.name == u'posix':
        default_dir = path.join(
            path.expanduser('~'),
            '.steam/steam/steamapps/common/dota 2 beta/game/dota/server_log.txt'
            )
    else:
        default_dir = None #TODO

    parser.add_argument('-D', '--debug', dest='DEBUG', nargs='*', default=[])
    parser.add_argument('-f', '--file', dest='server_log', default=None,
        help='TODO')

    args, unknown = parser.parse_known_args()

    client = requests.session()
    heroes = Json2Obj(
        json.loads(
            call_api(
                'https://api.stratz.com/api/v1/Hero'
            ).text
        )
    )
    for hero in heroes.__dict__.values():
        hero.icon = os.path.join(
            os.getcwd(),
            'icons', 'hero',
            hero.uri+'.png'
        )
        if not os.path.exists(hero.icon):
            print(hero.displayName)

    if not args.server_log:
        #TODO: Load config
        args.server_log = default_dir

    if 'immediate' in args.DEBUG:
        matches = parse_server_log(args.server_log)
        #last_match = matches[-1]

        for match in matches[-1:0:-1]: #tqdm(matches[-1:0:-1], desc='Parsing matches...'):
            for player_id in match:#tqdm(match, desc='Parsing players...'):
                p = Player(player_id, **match_filter)
                print('{:30s}\t{}\t{:.2f}({:.2f})'.format(p.name, p.matchCount, p.winrate, p.behavior.winrate))
                #p.heroAlert
                continue
            break
            #continue

    else:
        while True:
            matches = FileModifiedHandler(
                path.dirname(path.realpath(args.server_log)),
                path.basename(args.server_log),
                parse_server_log)
            for match in matches[-1:0:-1]: #tqdm(matches[-1:0:-1], desc='Parsing matches...'):
                for player_id in match:#tqdm(match, desc='Parsing players...'):
                    p = Player(player_id, **match_filter)
                    print('{:30s}\t{}\t{:.2f}({:.2f})'.format(p.name, p.matchCount, p.winrate, p.behavior.winrate))
                    #p.heroAlert
                    continue
                break
            #continue

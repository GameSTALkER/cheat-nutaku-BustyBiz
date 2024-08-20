from client import BustyBizClient
import json


class ConsoleCommandsInterpriter:
    def __init__(self, client: BustyBizClient):
        self.client = client
        self.last_elevator = None
        self.register_if_not_exist = False
        self.commands = {
            "sync": self.sync,
            "setcurrency": self.setcurrency,
            "unlockscene": self.unlockscene,
            "unlockmansion": self.unlockmansion,
            "claimdaily": self.claimdaily,
            "claimbox": self.claimbox,
            "claimbooster": self.claimbooster,
            "claimall": self.claimall,
            "claimeventbox": self.claimeventbox,
            "addeventclicks": self.addeventclicks,
            "addec": self.addeventclicks,  # Alias
            "opengacha": self.opengacha,
            "enterelevator": self.enterelevator,
            "runelevator": self.runelevator,
            "drawelevator": self.drawelevator,
            "collectseasonreward": self.collectseasonreward,
            "csr": self.collectseasonreward,  # Alias
            "claimmilestone": self.claimmilestone,
            "cm": self.claimmilestone,  # Alias
            "collectcash": self.collectcash,
            "cc": self.collectcash,  # Alias
            "setsessionid": self.setsessionid,
            "setuserid": self.setuserid,
            "login": self.login,
            "log": self.login,  # Alias
            "relogin": self.relogin,
            "relog": self.relogin,  # Alias
            "toggleregister": self.toggleregister,
            "toggleregistration": self.toggleregister,  # Alias
            "tglreg": self.toggleregister,  # Alias
            "resetprogress": self.resetprogress,
            "deleteaccount": self.deleteaccount,
            "settutorialstep": self.settutorialstep,
            "setts": self.settutorialstep,  # Alias
            "collectfloorrewards": self.collectfloorrewards,
            "cfr": self.collectfloorrewards,  # Alias
            "unlockskills": self.unlockskills,
        }

    def _proceed_command(self, raw_command: str):
        if raw_command == "" or "_proceed_command" in raw_command:
            return

        args = raw_command.split(" ")
        command = args.pop(0)

        if command not in self.commands:
            print("Command not found")
            return

        _args = []
        for arg in args:
            if arg.lower() == "true":
                _args.append(True)
            elif arg.lower() == "false":
                _args.append(False)
            elif arg.isdigit():
                _args.append(int(arg))
            else:
                _args.append(arg)

        self.commands[command](_args)

    def sync(self, args):
        data = None
        if len(args) > 1 and args[1]:
            data = json.load("./save-settings.json")

        self.client.sync_game(args[0], data)

    def setcurrency(self, args):
        economy_data = self.client.areas.copy()
        for data in economy_data:
            if data["id"] == args[0]:
                data["bank_amount"] = args[1]
                break
        self.client.sync_game(100, economy_data=economy_data)

    def unlockscene(self, args):
        self.client.unlock_scene(*args)

    def unlockmansion(self, args):
        self.client.unlock_mansion(*args)

    def claimdaily(self, args=None):
        self.client.claim_daily()

    def claimbox(self, args=None):

        self.client.claim_free_giftbox()

    def claimbooster(self, args=None):
        self.client.claim_free_booster()

    def claimall(self, args=None):
        self.client.claim_daily()
        self.client.open_gacha(True, False)
        self.client.claim_free_giftbox()
        self.client.claim_free_booster()

    def claimeventbox(self, args):
        self.client.claim_event_box(*args)

    def addeventclicks(self, args):
        self.client.add_event_clicks(*args)

    def opengacha(self, args):
        self.client.open_gacha(*args)

    def enterelevator(self, args):
        self.last_elevator = args[0]

    def runelevator(self, args=None):
        if self.last_elevator is None:
            print("Run first: enterelevator 'elevator_event_id'")
            return
        return self.client.elevator_run(self.last_elevator)

    def drawelevator(self, args=None):
        if self.last_elevator is None:
            print("Run first: enterelevator 'elevator_event_id'")
            return
        return self.client.elevator_draw(self.last_elevator)

    def collectseasonreward(self, args):
        if len(args) == 1:
            args.append(False)
        if "-" in str(args[0]):
            raw = args[0].split("-")
            current = int(raw[0])
            end = int(raw[1])
            while current <= end:
                self.client.collect_season_rewards(current, args[1])
                current += 1
            return

        self.client.collect_season_rewards(*args)

    def claimmilestone(self, args):
        self.client.claim_quest_milestone_reward(args[0])

    def collectcash(self, args):
        self.client.collect_tower_idle_reward(*args)

    def setsessionid(self, args):
        if not isinstance(args[0], str):
            print("1st arg must be str")
            return
        self.client.user["session_id"] = args[0]

    def setuserid(self, args):
        if not isinstance(args[0], int):
            print("1st arg must be int")
            return
        self.client.user["id"] = args[0]

    def login(self, args):
        if "-" in str(args[0]):
            raw = args[0].split("-")
            current = int(raw[0])
            end = int(raw[1])
            while current <= end:
                self.client = BustyBizClient(current)
                if self.client.logged_in:
                    print("Login task stopped at", current)
                    return
                current += 1
            return

        self.client = BustyBizClient(*args)

    def relogin(self, args=None):
        self.client = BustyBizClient(self.client.nutaku_id)

    def toggleregister(self, args=None):
        print("Auto registration allowed:",
              self.client.change_register_if_not_exist()
              )

    def resetprogress(self, args=None):
        self.client.restart_progress()

    def deleteaccount(self, args=None):
        self.client.delete_account()

    def settutorialstep(self, args):
        self.client.set_tutorial_step(*args)

    def collectfloorrewards(self, args):
        if "-" in str(args[1]):
            raw = args[1].split("-")
            current = int(raw[0])
            end = int(raw[1])
            while current <= end:
                self.client.collect_floor_rewards(args[0], current)
                current += 1
            return
        self.client.collect_floor_rewards(*args)

    def unlockskills(self, args=None):
        self.client.unlock_skills()

import requests
import hashlib
import datetime
import json
import urllib.parse

class BustyBizClient:
    def __init__(self, nutaku_id: int) -> None:
        '''Last edit at: 20.08.2024\n
        have fucking no protection, what you need is only nutaku id...
        '''
        self.request_url = "https://game-nutaku.bustybiz.com/request.php"
        self.nutaku_id = nutaku_id

        print("\n\nTrying to log-in in with", self.nutaku_id, "nutaku id...")
        self.logged_in = False
        self.register_if_not_exist = False
        self.allow_unsafe_functions = False
        self.client_version = 'html5_1.74.595'

        self.full_data = {}
        self.user = {}
        self.character = {}
        self.active_events = []
        self.game = {}
        self.areas = []  # aka economy_data
        self.mansions = []
        self.current_tower_id = 0

        self._generate_session_key()

        self._headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://osapi.nutaku.com",
            "Referer": "https://osapi.nutaku.com/"
        }

        if not self.logged_in:
            print("Invalid.")
            return

        print("👤 Logged in as:", self.character["name"], "| user_id:",
              self.user["id"], "| session_id:", self.user["session_id"])
        print("🎉 Account created at", datetime.datetime.fromtimestamp(
            self.user["ts_creation"]))
        unlocked_towers = [
            tower["id"]
            for tower in self.game["towers"] if tower["id"] != self.current_tower_id
        ]
        print("🗼 Current tower id:", self.current_tower_id,
              "| Unlocked towers:", unlocked_towers)
        print("💎 Gems:", self.user["premium_currency"])
        print("🪙  Tournament Tokens:", self.character["tournament_tokens"])
        print("💵 Cash:", self.areas)

        # 0: Mountain cash
        # 1: City cash
        # 2: Desert cash
        # 3: Girl cash
        # 4:
        # 5:

        problematic_towers = []
        for tower in self.game["towers"]:
            for check in ["vault", "elevator", "regions", "floors", "manager_pool"]:
                if check not in tower:
                    problematic_towers.append(tower["id"])
                    break

        if len(problematic_towers) > 0:
            print(f"⚠️  DETECTED PROBLEMATIC TOWERS: {problematic_towers}")

        server_time = datetime.datetime.fromtimestamp(
            self.full_data["server_time"] - 1*24*60*60)
        dailyreward = datetime.datetime.fromtimestamp(
            self.game["ts_last_daily_reward_claimed"])
        dailyreward = dailyreward < server_time

        freegacha = datetime.datetime.fromtimestamp(
            self.game["gacha"]["ts_last_free_gacha"])
        freegacha = freegacha < server_time
        freebox = self.game["has_free_gift_box_available"]
        freebooster = self.game["inventory"]["has_free_booster_gacha_available"]
        if dailyreward or freegacha or freebox or freebooster:
            print("💰 Unclaimed daily rewards:")
            for key, value in {
                "Daily reward": dailyreward,
                "Free gacha": freegacha,
                "Free giftbox": freebox,
                "Free booster": freebooster
            }.items():
                if value:
                    print(" 🏆", key)

        if len(self.active_events) > 0:
            print("⭐ Active events ids:")
            for event in self.active_events:
                count = None
                if "elevator" not in event:
                    for item in self.game["inventory"]["items"]:
                        if item["item_id"] == "event_token_" + event:
                            count = item["amount"]
                            break

                sub_text = count and "| " + str(count) + " ❤️" or ""
                print(" 🎇", event, sub_text)

    def payload(self, **kwargs) -> dict:
        payload = dict(
            # event_id = "",
            # action = "",

            user_id=self.user["id"],
            user_session_id=self.user["session_id"],
            # auth = auth,

            client_version=self.client_version,
            device_type='web',
            rct=1
        )
        action = kwargs.get("action", None)

        for key, value in kwargs.items():
            payload.update({key: value})

        if action:
            payload["auth"] = self._generate_auth_key(action)

        return payload

    def payloadAlt(self, **kwargs) -> str:
        payload = self.payload(**kwargs)
        payload_data = []
        for key, value in payload.items():
            if isinstance(value, bool):
                value = str(value).lower()
            elif isinstance(value, dict) or isinstance(value, list):
                value = urllib.parse.quote(json.dumps(value))
            payload_data.append(key + "=" + str(value))
        return "&".join(payload_data)

    def change_register_if_not_exist(self) -> bool:
        self.register_if_not_exist = not self.register_if_not_exist
        return self.register_if_not_exist

    def _generate_session_key(self):
        methods = self.register_if_not_exist and [
            "loginUserSSO", "registerUserSSO"] or ["loginUserSSO"]

        for method in methods:
            payload = dict(
                platform="nutaku",
                platform_user_id=self.nutaku_id,
                device_id="web",
                action=method,
                auth=self._generate_auth_key(method, 0),
                client_version=self.client_version,
                device_info={"language": "en", "pixelAspectRatio": 1, "screenDPI": 72, "screenResolutionX": 2560,
                             "screenResolutionY": 1440, "touchscreenType": 0, "os": "HTML5", "version": "WEB 8,9,7,0"},
                user_id=0,
                user_session_id=0,
                rct=1,

                registration_source="",
                login_existing_user=True,
                device_advertisment_id=""
            )

            response = requests.post(self.request_url, data=payload)
            data = self._format_response(response)

            if isinstance(data, dict):
                if method == "registerUserSSO":

                    print("Registering...")
                self.logged_in = True

                self.full_data = data
                self.user = self.full_data["user"]
                self.character = self.full_data["character"]
                self.character["game_data"] = json.loads(
                    self.character["game_data"])
                self.active_events = self.full_data["current_event_ids"]
                self.game = self.character["game_data"]
                self.areas = self.game["areas"]
                self.mansions = self.game["mansion"]
                self.current_tower_id = self.game["active_tower_id"]
                return
            print(data)

    def _generate_auth_key(self, action: str, forced_user_id: int = None):
        '''Last edit at: 19.08.2024\n
        action + 'str' + (user_id or 'null')
        '''
        user_id = self.user["id"] if forced_user_id is None else forced_user_id
        user_id = "null" if isinstance(user_id, bool) else str(user_id)
        combined_string = action + "U4h4c64tQ" + user_id
        return hashlib.md5(combined_string.encode()).hexdigest()

    def _format_response(self, response: requests.Response):
        '''Last edit at: 19.08.2024\n
        '''
        raw = response.json()
        data = len(raw["data"]) != 0 and raw["data"] or None
        error = raw["error"] != 0 and raw["error"] or None

        if data:
            if "user" in data:
                self.user["premium_currency"] = data["user"]["premium_currency"]
            return data
        elif error:
            match error:
                case "errClaimEventBoxNotYetAvailable":
                    return "Not yet available."
                case "errRequestHandlerException":
                    return "Session expired (relogin or relog)."
                case "errRequestOutdatedClientVersion":
                    return "Headers client version outdated, update headers version."
                case "errUserNotAuthorized":
                    return "Update authorization key."
                case "errUseItemNotEnough":
                    return "Not enough items."
                case "errClaimRewardsInvalidStatus":
                    return "Task is not completed."
                case "errInvalidTask":
                    return "Invalid task."
                case "errInvalidArguments":
                    return "Invalid arguments."
                case "errCollectSeasonObjectiveRewardsAlreadyCollected":
                    return "Reward already collected."
                case "errCollectSeasonObjectiveRewardsInvalidObjectiveIndex":
                    return "Invalid reward index."
            return error

        return "Unexpected error occured."

    def claim_event_box(self, event_id: str):
        '''Last edit at: 19.08.2024\n
        `event_id`: 'nutaku_august_promo'
        '''
        payload = self.payload(
            action='claimEventBox',
            event_id=event_id
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Opened event box, now have:", list(
                data["event_box"]["rewards"].keys())[-1], "event clickers.")

    def sync_game(self, tower_id: int, tower_data: dict = None, economy_data: dict = None):
        '''Last edit at: 19.08.2024\n
        '''
        if not tower_data:
            for tower in self.game["towers"]:
                if tower["id"] == tower_id:
                    tower_data = tower
                    break

        payload = self.payloadAlt(
            action="syncGame",
            tower_id=tower_id,
            tower_data=tower_data,
            economy_data=economy_data or self.areas,
            metrics=None,
            sync_all=False
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("New data has been saved")

    def _enter_tower(self, tower_id: int, old_tower_data: dict = None):
        '''Last edit at: 20.08.2024\n
        `UNSAFE` - MAY BREAK YOUR GAME (Only for now)
        '''
        if not self.allow_unsafe_functions:
            print("_enter_tower is UNSAFE function")
            return

        if not old_tower_data:
            for tower in self.game["towers"]:
                if tower["id"] == self.current_tower_id:
                    old_tower_data = tower
                    break

        payload = self.payloadAlt(
            action="enterTower",
            old_tower_id=self.current_tower_id,
            old_tower_data=old_tower_data,
            new_tower_id=tower_id,
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
            return False
        else:
            print("Entered tower ", tower_id)
            self.current_tower_id = tower_id
            return True

    def collect_tower_idle_reward(self, tower_id: int):
        '''Last edit at: 20.08.2024\n
        '''
        if self.allow_unsafe_functions:
            state = self._enter_tower(tower_id)

            if not state:
                return

        payload = self.payload(
            action="collectTowerIdleReward",
            tower_id=tower_id,
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print(f"Collected rewards and got from tower {tower_id}:",
                  data["reward_amount"] if data["reward_amount"] != 0 else "?")

    def use_item(self, item_id: int, amount: int = 1):
        '''Last edit at: 19.08.2024\n
        '''

        payload = self.payload(
            action="useInventoryItem",
            item_id=item_id,
            type=0,
            amount=amount
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Item consumed.")

    def start_event(self, event_id: str):
        '''Last edit at: 20.08.2024\n
        '''

        payload = self.payload(
            action="startEvent",
            event_id=event_id,
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Event", event_id, "started")

    def add_event_clicks(self, event_id: str, clicks: int):
        '''Last edit at: 19.08.2024\n
        Works even without using click item and have no server side checks about clicks\n
        You can enter the maximum needed clicks count (25k by default) and you'll get all rewards\n
        '''

        payload = self.payload(
            action="addClickerEventClicks",
            event_id=event_id,
            clicks=clicks,
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            if data == "errAddClickerEventClicksInvalidEventId":
                self.start_event(event_id)
                return
            print(data)
        else:
            print("Clicker event completed.")

    def complete_task(self, task_id: int):
        '''Last edit at: 19.08.2024\n
        '''

        payload = self.payload(
            action="collectTaskReward",
            task_id=task_id
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Task completed.\n", data["tasks"])

    def start_purchase(self, offer_identifier: str, amount: int):
        '''Last edit at: 19.08.2024\n
        '''

        payload = self.payload(
            action="initConsumableOfferPayment",
            offer_identifier=offer_identifier,
            amount=amount,
            payment_method=111,
            is_gift=False,
            locale="en_US",
            currency="USD"
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Purchase started with id", data["payment_id"])
            return data["payment_id"]

    def complete_purchase(self, payment_id: int):
        '''Last edit at: 19.08.2024\n
        '''

        payload = self.payload(
            action="finalizeNutakuPayment",
            payment_id=payment_id,
            callback_status=0
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Purchase completed.")

    def open_gacha(self, free: bool, multi: bool):
        '''Last edit at: 19.08.2024\n
        '''

        payload = self.payloadAlt(
            action="getGachaReward",
            free=free,
            multi=multi
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print(data["gacha_rewards"])

    def elevator_run(self, event_id: str):
        '''Last edit at: 19.08.2024\n
        `event_id` - 'nutaku_august_promo_elevator'
        '''

        payload = self.payload(
            action="continueLuckyElevatorRun",
            event_id=event_id
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            floor_level = int(
                data["event"]["lucky_elevator_run"]["current_floor_id"].split("_")[-1])
            print("Current floor is:", floor_level)

    def elevator_draw(self, event_id: str):
        '''Last edit at: 19.08.2024\n
        `event_id` - 'nutaku_august_promo_elevator'
        '''

        payload = self.payload(
            action="drawLuckyElevatorReward",
            event_id=event_id
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Reward:", data["event"]
                  ["lucky_elevator_run"]["last_picked_reward_id"])

    def collect_season_rewards(self, objective_index: int, is_season_pass_reward: bool = False):
        '''Last edit at: 19.08.2024\n
        Works only if opened reward\n
        season pass rewards can be obtained without the pass
        '''
        payload = self.payloadAlt(
            action="collectSeasonObjectiveRewards",
            objective_index=objective_index,
            is_season_pass_reward=is_season_pass_reward
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Collected object", objective_index,
                  is_season_pass_reward and "from pass" or "")

    def claim_daily(self):
        '''Last edit at: 19.08.2024\n
        '''
        payload = self.payload(
            action="collectDailyReward"
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Daily claimed.")

    def claim_free_giftbox(self):
        '''Last edit at: 19.08.2024\n
        '''
        payload = self.payload(
            action="claimFreeGiftBox"
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Daily free giftbox.")

    def claim_free_booster(self):
        '''Last edit at: 19.08.2024\n
        '''
        payload = self.payload(
            action="claimFreeBoosterGacha"
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Daily free booster.")

    def unlock_scene(self, girl: str, scene_index: int):
        '''Last edit at: 19.08.2024\n
        '''
        payload = self.payload(
            action="unlockInteractiveScene",
            interactive_scene_id=girl.lower() + "_scene" + str(scene_index)
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Scene", girl + str(scene_index), "unlocked.")

    def collect_floor_rewards(self, tower_id: int, floor_id: int, objective_key: int = 100):
        '''Last edit at: 19.08.2024\n
        `floor_id`: 1-30
        '''
        obj_id = "reach_floor" + str(floor_id)
        for obj in [
            "_lvl1000",
            "_lvl875",
            "_lvl750",
            "_lvl625",
            "_lvl500",
            "_lvl375",
            "_lvl250",
            "_lvl125",
            "_lvl60",
            "_lvl30",
            "_lvl10",
            "",
        ]:
            payload = self.payload(
                action="collectTowerObjectiveReward",
                tower_id=tower_id,
                objective_id=obj_id+obj,
                objective_key=objective_key
            )
            response = requests.post(
                self.request_url, data=payload, headers=self._headers)
            data = self._format_response(response)

            if isinstance(data, str):
                print(data)
                break
            else:
                print("Claimed")

    def unlock_mansion(self, building_id: str):
        '''Last edit at: 19.08.2024\n
        '''
        for action in ["startLevelUpMansionBuilding", "unlockMansionBuildingLevel"]:
            payload = self.payload(
                action=action,
                mansion_building_id=building_id,
                economy_data=self.areas
            )
            response = requests.post(
                self.request_url, data=payload, headers=self._headers)
            data = self._format_response(response)

            if isinstance(data, str):
                print(data)
                break
            else:
                print(data)
                print("Unlocking: " + building_id if action ==
                      "startLevelUpMansionBuilding" else "Unlocked: " + building_id)

    def claim_quest_milestone_reward(self, milestone: int):
        '''Last edit at: 20.08.2024\n
        `milestone`: 1-10
        '''
        payload = self.payload(
            action="collectQuestPartyMilestoneReward",
            milestone=milestone,
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Collected reward")

    def set_tutorial_step(self, step: int):
        '''Last edit at: 20.08.2024\n
        '''
        payload = self.payload(
            action="setTutorialStep",
            tutorial_step=step
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Completed")

    def delete_account(self):
        '''Last edit at: 20.08.2024\n
        `UNSAFE` - ACCOUNT CAN BE DELETED
        '''
        if not self.allow_unsafe_functions:
            print("delete_account is UNSAFE function")
            return

        payload = self.payload(
            action="deleteUser",
            password="",
            request_reactivation_code=True
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Account deleted, reactivation code:",
                  data["reactivation_code"])

    def restart_progress(self):
        '''Last edit at: 20.08.2024\n
        `UNSAFE` - RESTART YOUR PROGRESS
        '''
        if not self.allow_unsafe_functions:
            print("restart_progress is UNSAFE function")
            return

        payload = self.payload(
            action="resetProgress",
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Account progress reseted.")

    def unlock_skills(self):
        '''Last edit at: 20.08.2024\n
        '''
        payload = self.payload(
            action="unlockSkills",
            economy_data=self.areas
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Skills tree is now unlocked")

    def upgrade_skill(self, skill_id: int):
        '''Last edit at: 20.08.2024\n
        1-99 - Green skills\n
        100-199 - Blue skills\n
        200-299 - Red skills
        '''
        payload = self.payload(
            action="startLevelUpSkill",
            skill_id=skill_id
        )
        response = requests.post(
            self.request_url, data=payload, headers=self._headers)
        data = self._format_response(response)

        if isinstance(data, str):
            print(data)
        else:
            print("Skills tree is now unlocked")

from consolecommands import ConsoleCommandsInterpriter
from client import BustyBizClient

# register_if_not_exist = False ----- Say no to global vars
# allow_unsafe_functions = False
# default_nutaku_id = None
CLIENT_VERSION = 'html5_1.74.595'

# TODO
# better sync (in self._format_response)
# fix self._enter_tower


if __name__ == "__main__":
    # client = BustyBizClient(default_nutaku_id or
    #                      input("Enter your nutaku_id > "))
    client = BustyBizClient(input("Enter your nutaku_id > "), CLIENT_VERSION)
    console_interpriter = ConsoleCommandsInterpriter(client)
    last_elevator = None

    while True:
        try:
            command = console_interpriter._proceed_command(input("> "))

        except KeyboardInterrupt:
            break

        except IndexError:
            print("You must specify one more argument.")

    # client.use_item("4a685612e33b3229cbc89bb38abd49a2", 172147303, 10) # Work
    # client.complete_task("3d63b81adcbf5388dd0efd236328ceac", 12163304) # Work

    # payment_id = client.start_purchase("eb06dc8b4d41c599eaf0afb6a243a3c4", "premium1", 199)
    # client.complete_purchase("399efe1863624b705b020de57ac8c484", payment_id)
    #

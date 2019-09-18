from bp_chat.run import main
from bp_chat.logic.common.tryable import run_in_try

if __name__ == '__main__':
    run_in_try(main)
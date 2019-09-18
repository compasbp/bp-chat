import traceback, sys

def run_in_try(func):
    try:
        func()
    except BaseException as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        formatted_lines = traceback.format_exc().splitlines()

        fexc = traceback.format_exception(exc_type, exc_value,
                                          exc_traceback)

        fe_line = ''.join(fexc[2:])
        if ', line' not in fe_line:
            fe_line = ''.join(fexc)

        print(fe_line)
        
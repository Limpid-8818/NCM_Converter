import sys

from controller.cli_controller import CLIController


def main():
    controller = CLIController()
    status = controller.run()
    sys.exit(0 if status else 1)


if __name__ == "__main__":
    main()

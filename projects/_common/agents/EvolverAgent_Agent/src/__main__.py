#!/usr/bin/env python3
"""
EvolverAgent MVP Entry Point

This module serves as the main entry point for the EvolverAgent MVP.
It simply instantiates and runs the EvolverAgent.
"""

from .agent import EvolverAgent


def main():
    """Main entry point for the EvolverAgent."""
    agent = EvolverAgent()
    agent.run()


if __name__ == "__main__":
    main()

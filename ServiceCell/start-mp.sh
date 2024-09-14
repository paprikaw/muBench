#!/bin/bash

# note that the process of the service-cell (CellController.py) is run within a screen for easier debugging
# this may impair kubernetes ability to detect failures because CellController.py may crash within the screen without closing container
tmux new-session -d -s APP
tmux source-file /.tmux.conf
tmux rename-window -t APP:0 win0
tmux send-keys -t APP:win0 'prometheus_multiproc_dir=/app /usr/local/bin/python3 /app/CellController-mp.py' C-m
sleep infinity

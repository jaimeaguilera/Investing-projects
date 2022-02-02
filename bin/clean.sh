#!/bin/bash

PROJECT_DIR=`cd $(dirname $0) && cd .. && pwd`

source ${PROJECT_DIR}/script/setup.sh

isort npl_planner && flake8 npl_planner

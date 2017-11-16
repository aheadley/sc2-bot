#!/bin/bash

set -x

GAME_VERSION="$1"
DEST="$2"

##

DATA_URL_BASE="http://blzdistsc2-a.akamaihd.net"
CLIENT_FILE="Linux/SC2.${GAME_VERSION}.zip"
MAP_FILES=( "MapPacks/Ladder2017Season1.zip" "MapPacks/Ladder2017Season2.zip" "MapPacks/Ladder2017Season3.zip" "MapPacks/Melee.zip" )
DATA_PASSWORD='iagreetotheeula'
MAP_DEST="StarCraftII/Maps"

mkdir -p "${DEST}/${MAP_DEST}"

# we fetch and unpack the maps first, then skip the whole bit if the client
# unpack completed successfully
if ! [ -f "${DEST}/StarCraftII/Versions/Base56787/SC2_x64" ]; then
    for fn in "${MAP_FILES[@]}"; do
        wget --timestamping --continue -qO "/tmp/$(basename ${fn})" "${DATA_URL_BASE}/${fn}"
        unzip -n -P "${DATA_PASSWORD}" -d "${DEST}/${MAP_DEST}" "/tmp/$(basename ${fn})"
        rm -f "/tmp/$(basename ${fn})"
    done

    wget --timestamping --continue -qO "/tmp/$(basename ${CLIENT_FILE})" "${DATA_URL_BASE}/${CLIENT_FILE}"
    unzip -n -P "${DATA_PASSWORD}" -d "${DEST}" "/tmp/$(basename ${CLIENT_FILE})"
    rm -f "/tmp/$(basename ${CLIENT_FILE})"
fi

find "${DEST}/StarCraftII" -type d | xargs chmod 755
find "${DEST}/StarCraftII" -type f | xargs chmod 644
find "${DEST}/StarCraftII/Libs" -type f | xargs chmod 755
find "${DEST}/StarCraftII/Versions" -type f | xargs chmod 755

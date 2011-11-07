
function fudepan-install {
    sudo scons INSTALL_HEADERS_DIR=/usr/local/include/ INSTALL_BIN_DIR=/usr/local/bin/ INSTALL_LIB_DIR=/usr/local/lib/ $* install
}


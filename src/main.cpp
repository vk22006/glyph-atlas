#include "app-window.h"

int main(int argc, char **argv) {
    auto app = AppWindow::create();
    app->run();
    return 0;
}

#include <spdlog/spdlog.h>

int main(int argc, char *argv[]){
	spdlog::info("Hello, waf! {}", argv[0]);
	return 0;
}
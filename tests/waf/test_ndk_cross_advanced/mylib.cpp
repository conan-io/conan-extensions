#include "car_generated.h"
#include <flatbuffers/flatbuffers.h>
#include <cinttypes>
#include <fstream>
#include <android/log.h>

#define LOGI(...) ((void)__android_log_print(ANDROID_LOG_INFO, "mylib", __VA_ARGS__))

using namespace Test;

void read_car(const char *filename){
	std::ifstream file(filename, std::ios_base::binary);
	file.seekg(0, std::ios_base::end);
	size_t length = file.tellg();
	void *data = malloc(length);
	file.seekg(0);
	file.read((char*)data, length);
	auto car = GetCar(data);
	LOGI("Model: (%s)", car->model()->c_str());
	LOGI("Year: (%d)", (int)car->year());
	LOGI("Make: %s (%d)", car->make()->name()->c_str(), (int)car->make()->coolness());
	file.close();
	free(data);
}

void write_car(
	const char *filename,
	const char *make,
	const char *model,
	uint16_t year,
	uint8_t coolness
){
	flatbuffers::FlatBufferBuilder builder(1024);
	auto mfname = builder.CreateString(make);
	auto mf = CreateManufacturer(builder, mfname, coolness);
	auto m = builder.CreateString(model);
	auto car = CreateCar(builder, mf, m, year);
	builder.Finish(car);

	uint8_t *buf = builder.GetBufferPointer();
	int size = builder.GetSize();
	std::ofstream file(filename, std::ios_base::binary);
	file.write((char*)buf, size);
	file.close();
}
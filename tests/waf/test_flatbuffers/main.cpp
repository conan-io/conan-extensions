#include "car_generated.h"
#include <flatbuffers/flatbuffers.h>
#include <cinttypes>
#include <fstream>
#include <iostream>

using namespace Test;

void read_buf(const char *filename){
	std::ifstream file(filename, std::ios_base::binary);
	file.seekg(0, std::ios_base::end);
	size_t length = file.tellg();
	void *data = malloc(length);
	file.seekg(0);
	file.read((char*)data, length);
	auto car = GetCar(data);
	std::cout << "Model: " << car->model()->c_str() << std::endl;
	std::cout << "Year: " << car->year() << std::endl;
	std::cout << "Make: " << car->make()->name()->c_str();
	std::cout << " (" << (int)car->make()->coolness() << ")" << std::endl;
	file.close();
	free(data);
}

void write_buf(
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

int main(int argc, char *argv[]){
	//write
	write_buf("car1.bin", "McCar", "Nugget", 2033, 22);
	write_buf("car2.bin", "Car King", "Flopper", 2032, 43);

	//read
	read_buf("car1.bin");
	std::cout << "-----" << std::endl;
	read_buf("car2.bin");
	return 0;
}
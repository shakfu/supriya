#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/pair.h>
#include <stdexcept>

#include "server_shm.hpp"

namespace nb = nanobind;

using detail_server_shm::server_shared_memory_client;
using detail_server_shm::scope_buffer_reader;

class ServerSHM {
    server_shared_memory_client* client;
    unsigned int bus_count;

public:
    ServerSHM(unsigned int port_number, unsigned int bus_count)
        : client(new server_shared_memory_client(port_number)),
          bus_count(bus_count) {}

    ~ServerSHM() {
        delete client;
    }

    // Non-copyable
    ServerSHM(const ServerSHM&) = delete;
    ServerSHM& operator=(const ServerSHM&) = delete;

    float get_bus(int index) const {
        if (index < 0 || static_cast<unsigned int>(index) >= bus_count)
            throw std::out_of_range("index out of bounds");
        return client->get_control_busses()[index];
    }

    std::vector<float> get_bus_range(int start, int stop, int step) const {
        std::vector<float> result;
        float* busses = client->get_control_busses();
        for (int i = start; i < stop; i += step) {
            result.push_back(busses[i]);
        }
        return result;
    }

    void set_bus(int index, float value) {
        if (index < 0 || static_cast<unsigned int>(index) >= bus_count)
            throw std::out_of_range("index out of bounds");
        client->set_control_bus(index, value);
    }

    void set_bus_range(int start, int stop, int step, const std::vector<float>& values) {
        int vi = 0;
        for (int i = start; i < stop; i += step) {
            client->set_control_bus(i, values[vi++]);
        }
    }

    std::pair<unsigned int, unsigned int> describe_scope_buffer(unsigned int index) {
        scope_buffer_reader reader = client->get_scope_buffer_reader(index);
        if (!reader.valid())
            throw std::runtime_error("Invalid scope buffer");
        return {reader.channels(), reader.max_frames()};
    }

    std::pair<unsigned int, std::vector<float>> read_scope_buffer(unsigned int index) {
        scope_buffer_reader reader = client->get_scope_buffer_reader(index);
        if (!reader.valid())
            throw std::runtime_error("Invalid scope buffer");
        unsigned int available_frames = 0;
        reader.pull(available_frames);
        float* data = reader.data();
        std::vector<float> pydata(data, data + 8192);
        return {available_frames, pydata};
    }

    unsigned int get_bus_count() const { return bus_count; }
};

NB_MODULE(_shm, m) {
    m.doc() = "Server shared memory interface";

    nb::class_<ServerSHM>(m, "ServerSHM")
        .def(nb::init<unsigned int, unsigned int>(),
             nb::arg("port_number"), nb::arg("bus_count"))
        .def("get_bus", &ServerSHM::get_bus, nb::arg("index"))
        .def("get_bus_range", &ServerSHM::get_bus_range,
             nb::arg("start"), nb::arg("stop"), nb::arg("step"))
        .def("set_bus", &ServerSHM::set_bus,
             nb::arg("index"), nb::arg("value"))
        .def("set_bus_range", &ServerSHM::set_bus_range,
             nb::arg("start"), nb::arg("stop"), nb::arg("step"), nb::arg("values"))
        .def("describe_scope_buffer", &ServerSHM::describe_scope_buffer, nb::arg("index"))
        .def("read_scope_buffer", &ServerSHM::read_scope_buffer, nb::arg("index"))
        .def_prop_ro("bus_count", &ServerSHM::get_bus_count);
}

/*
 * SPDX-FileCopyrightText: 2026 M5Stack Technology CO LTD
 *
 * SPDX-License-Identifier: MIT
 */
#pragma once
#include "../gcp_model.h"
#include <functional>
#include <string>

namespace gcp_monitor {

class GcpClient {
public:
    GcpClient();
    ~GcpClient();

    void setEndpoint(const std::string& url);
    const std::string& getEndpoint() const { return _endpoint; }

    // Synchronous or cached fetch
    bool fetchTelemetry(GcpTelemetry& telemetry);

    // Get latest cached data
    const GcpTelemetry& getCachedTelemetry() const { return _cached_data; }

private:
    std::string _endpoint;
    GcpTelemetry _cached_data;
    uint32_t _last_fetch_ms;
};

} // namespace gcp_monitor

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

    void setApiKey(const std::string& key);
    const std::string& getApiKey() const { return _api_key; }

    // Synchronous or cached fetch
    bool fetchTelemetry(GcpTelemetry& telemetry);

    // Get latest cached data
    const GcpTelemetry& getCachedTelemetry() const { return _cached_data; }

private:
    std::string _endpoint;
    std::string _api_key;
    GcpTelemetry _cached_data;
    uint32_t _last_fetch_ms;
};

} // namespace gcp_monitor

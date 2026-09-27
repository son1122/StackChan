/*
 * SPDX-FileCopyrightText: 2026 M5Stack Technology CO LTD
 *
 * SPDX-License-Identifier: MIT
 */
#pragma once
#include <mooncake.h>
#include "gcp_model.h"
#include "services/gcp_client.h"
#include "view/gcp_monitor_view.h"
#include <memory>

class AppGcpMonitor : public mooncake::AppAbility {
public:
    AppGcpMonitor();

    void onCreate() override;
    void onOpen() override;
    void onRunning() override;
    void onClose() override;

private:
    std::unique_ptr<gcp_monitor::GcpClient> _client;
    std::unique_ptr<gcp_monitor_view::GcpMonitorView> _view;
    gcp_monitor::GcpTelemetry _telemetry;
    uint32_t _last_poll_ms;
    uint32_t _last_touch_ms;
    uint32_t _last_motion_ms;
    int _head_touch_conn;
    bool _event_head_tap;
};

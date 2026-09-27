/*
 * SPDX-FileCopyrightText: 2026 M5Stack Technology CO LTD
 *
 * SPDX-License-Identifier: MIT
 */
#include "app_gcp_monitor.h"
#include <hal/hal.h>
#include <mooncake_log.h>
#include <assets/assets.h>
#include <stackchan/stackchan.h>
#include "../common/common.h"

using namespace mooncake;
using namespace gcp_monitor;

AppGcpMonitor::AppGcpMonitor()
    : _last_poll_ms(0),
      _last_touch_ms(0),
      _last_motion_ms(0)
{
    setAppInfo().name = "GCP Monitor";
    static auto icon  = assets::get_image("icon_sentinel.bin");
    setAppInfo().icon = (void*)&icon;
    static uint32_t theme_color = 0x4285F4; // Google Cloud Blue
    setAppInfo().userData       = (void*)&theme_color;
}

void AppGcpMonitor::onCreate()
{
    mclog::tagInfo(getAppInfo().name, "on create");
}

void AppGcpMonitor::onOpen()
{
    mclog::tagInfo(getAppInfo().name, "on open");

    LvglLockGuard lock;

    _client = std::make_unique<GcpClient>();
    _view   = std::make_unique<gcp_monitor_view::GcpMonitorView>();
    _view->init();

    // Fetch initial data
    _client->fetchTelemetry(_telemetry);
    _view->update(_telemetry);

    // Setup home indicator for easy navigation back to launcher
    ::view::create_home_indicator([this]() { close(); }, 0x38BDF8, 0x0F172A);

    _last_poll_ms = GetHAL().millis();
    _last_motion_ms = GetHAL().millis();
}

void AppGcpMonitor::onRunning()
{
    uint32_t now = GetHAL().millis();

    // 1. Touch interaction for paging (Tap Left = Prev Page, Tap Right = Next Page)
    lv_indev_t* indev = GetHAL().lvTouchpad;
    if (indev) {
        lv_indev_state_t state = lv_indev_get_state(indev);
        if (state == LV_INDEV_STATE_PR && (now - _last_touch_ms > 400)) {
            lv_point_t pt;
            lv_indev_get_point(indev, &pt);
            // Ignore bottom 40px reserved for HomeIndicator
            if (pt.y < 200) {
                _last_touch_ms = now;
                LvglLockGuard lock;
                if (pt.x < 160) {
                    _view->prevPage();
                } else {
                    _view->nextPage();
                }
                _view->update(_telemetry);
            }
        }
    }

    // 2. Periodic Telemetry Update (every 6 seconds)
    if (now - _last_poll_ms > 6000) {
        _last_poll_ms = now;
        _client->fetchTelemetry(_telemetry);
        LvglLockGuard lock;
        if (_view) {
            _view->update(_telemetry);
        }
    }

    // 3. Robot Motion & LED Reaction (every 4 seconds)
    if (now - _last_motion_ms > 4000) {
        _last_motion_ms = now;
        auto& motion = GetStackChan().motion();
        if (_telemetry.overall_status == "ok") {
            // Gentle nodding when healthy
            static bool toggle = false;
            motion.moveWithSpeed(0, toggle ? 180 : 0, 400);
            toggle = !toggle;
            GetStackChan().leftNeonLight().setColor(34, 197, 94);   // Google Green
            GetStackChan().rightNeonLight().setColor(34, 197, 94);
        } else if (_telemetry.overall_status == "warning") {
            // Head tilt on warning
            motion.moveWithSpeed(220, 100, 500);
            GetStackChan().leftNeonLight().setColor(245, 158, 11);  // Amber
            GetStackChan().rightNeonLight().setColor(245, 158, 11);
        } else {
            // Head shake on outage/incident
            static bool shake_dir = false;
            motion.moveWithSpeed(shake_dir ? -300 : 300, 50, 700);
            shake_dir = !shake_dir;
            GetStackChan().leftNeonLight().setColor(239, 68, 68);   // Red
            GetStackChan().rightNeonLight().setColor(239, 68, 68);
        }
    }

    {
        LvglLockGuard lock;
        ::view::update_home_indicator();
    }

    GetStackChan().update();
}

void AppGcpMonitor::onClose()
{
    mclog::tagInfo(getAppInfo().name, "on close");

    LvglLockGuard lock;
    ::view::destroy_home_indicator();
    _view.reset();
    _client.reset();

    // Turn off neon lights on exit
    GetStackChan().leftNeonLight().setColor(0, 0, 0);
    GetStackChan().rightNeonLight().setColor(0, 0, 0);
}

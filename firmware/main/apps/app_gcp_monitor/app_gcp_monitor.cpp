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

#if __has_include("gcp_secret_config.h")
#include "gcp_secret_config.h"
#endif

using namespace mooncake;
using namespace gcp_monitor;

AppGcpMonitor::AppGcpMonitor()
    : _last_poll_ms(0),
      _last_touch_ms(0),
      _last_motion_ms(0),
      _head_touch_conn(0),
      _event_head_tap(false)
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
#ifdef STACKCHAN_GCP_ENDPOINT
    _client->setEndpoint(STACKCHAN_GCP_ENDPOINT);
#endif
#ifdef STACKCHAN_GCP_API_KEY
    _client->setApiKey(STACKCHAN_GCP_API_KEY);
#endif
#ifdef STACKCHAN_GCP_AUTH_HEADER
    _client->setBasicAuth(STACKCHAN_GCP_AUTH_HEADER);
#endif
    _view   = std::make_unique<gcp_monitor_view::GcpMonitorView>();
    _view->init();

    // Fetch initial multi-project data
    _client->fetchTelemetry(_telemetry);
    _view->update(_telemetry);

    // Setup home indicator for easy navigation back to launcher
    ::view::create_home_indicator([this]() { close(); }, 0x38BDF8, 0x0F172A);

    // Bind Head Touch sensor (Si12T) to cycle projects
    _head_touch_conn = GetHAL().onHeadPetGesture.connect([this](HeadPetGesture gesture) {
        if (gesture == HeadPetGesture::Press || gesture == HeadPetGesture::SwipeForward) {
            _event_head_tap = true;
        }
    });

    _last_poll_ms = GetHAL().millis();
    _last_motion_ms = GetHAL().millis();
}

void AppGcpMonitor::onRunning()
{
    uint32_t now = GetHAL().millis();

    // 1. Head Touch Interaction: Cycle Projects
    if (_event_head_tap && (now - _last_touch_ms > 350)) {
        _event_head_tap = false;
        _last_touch_ms = now;
        LvglLockGuard lock;
        if (_view) {
            _view->nextProject((int)_telemetry.projects.size());
            _view->update(_telemetry);
        }
        // Robot acknowledges with a sharp nod and cyan glow
        GetStackChan().motion().moveWithSpeed(0, 150, 300);
        GetStackChan().leftNeonLight().setColor(56, 189, 248);  // Cyan
        GetStackChan().rightNeonLight().setColor(56, 189, 248);
    }

    // 2. Touch Screen Interaction
    lv_indev_t* indev = GetHAL().lvTouchpad;
    if (indev) {
        lv_indev_state_t state = lv_indev_get_state(indev);
        if (state == LV_INDEV_STATE_PR && (now - _last_touch_ms > 400)) {
            lv_point_t pt;
            lv_indev_get_point(indev, &pt);

            if (pt.y < 38) {
                // Tapping Header Bar: Switch Project
                _last_touch_ms = now;
                LvglLockGuard lock;
                if (_view) {
                    _view->nextProject((int)_telemetry.projects.size());
                    _view->update(_telemetry);
                }
                GetStackChan().motion().moveWithSpeed(0, 150, 300);
            } else if (pt.y < 200) {
                // Tapping Body: Left = Prev Page, Right = Next Page
                _last_touch_ms = now;
                LvglLockGuard lock;
                if (_view) {
                    if (pt.x < 160) {
                        _view->prevPage();
                        GetStackChan().motion().moveWithSpeed(-120, 0, 300); // Look left
                    } else {
                        _view->nextPage();
                        GetStackChan().motion().moveWithSpeed(120, 0, 300);  // Look right
                    }
                    _view->update(_telemetry);
                }
            }
        }
    }

    // 3. Periodic Telemetry Update (every 6 seconds)
    if (now - _last_poll_ms > 6000) {
        _last_poll_ms = now;
        _client->fetchTelemetry(_telemetry);
        LvglLockGuard lock;
        if (_view) {
            _view->update(_telemetry);
        }
    }

    // 4. Robot Motion & Ambient LED Reaction (every 4 seconds)
    if (now - _last_motion_ms > 4000) {
        _last_motion_ms = now;
        auto& motion = GetStackChan().motion();

        std::string current_status = _telemetry.overall_status;
        if (_view && _view->getCurrentProjectIndex() > 0 && !_telemetry.projects.empty()) {
            int p_idx = (_view->getCurrentProjectIndex() - 1) % _telemetry.projects.size();
            current_status = _telemetry.projects[p_idx].status;
        }

        if (current_status == "ok") {
            // Gentle nodding when healthy
            static bool toggle = false;
            motion.moveWithSpeed(0, toggle ? 180 : 0, 400);
            toggle = !toggle;
            GetStackChan().leftNeonLight().setColor(34, 197, 94);   // Google Green
            GetStackChan().rightNeonLight().setColor(34, 197, 94);
        } else if (current_status == "warning") {
            // Curious head tilt on warning
            motion.moveWithSpeed(220, 100, 500);
            GetStackChan().leftNeonLight().setColor(245, 158, 11);  // Amber
            GetStackChan().rightNeonLight().setColor(245, 158, 11);
        } else {
            // Anxious head shake on incident
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

    // Unbind head touch listener
    GetHAL().onHeadPetGesture.disconnect(_head_touch_conn);

    LvglLockGuard lock;
    ::view::destroy_home_indicator();
    _view.reset();
    _client.reset();

    // Turn off neon lights on exit
    GetStackChan().leftNeonLight().setColor(0, 0, 0);
    GetStackChan().rightNeonLight().setColor(0, 0, 0);
}

/*
 * SPDX-FileCopyrightText: 2026 M5Stack Technology CO LTD
 *
 * SPDX-License-Identifier: MIT
 */
#pragma once
#include "../gcp_model.h"
#include <hal/hal.h>
#include <smooth_lvgl.hpp>
#include <memory>

namespace gcp_monitor_view {

class GcpMonitorView {
public:
    GcpMonitorView();
    ~GcpMonitorView();

    void init();
    void update(const gcp_monitor::GcpTelemetry& data);
    void nextPage();
    void prevPage();
    void nextProject(int total_projects);
    void prevProject(int total_projects);

    int getCurrentPage() const { return _current_page; }
    int getCurrentProjectIndex() const { return _current_project_index; }
    void setCurrentProjectIndex(int idx) { _current_project_index = idx; }

private:
    void renderPage(const gcp_monitor::GcpTelemetry& data);
    void clearCards();

    std::unique_ptr<uitk::lvgl_cpp::Container> _root;
    std::unique_ptr<uitk::lvgl_cpp::Container> _header;
    std::unique_ptr<uitk::lvgl_cpp::Label> _title_label;
    std::unique_ptr<uitk::lvgl_cpp::Label> _status_badge;
    std::unique_ptr<uitk::lvgl_cpp::Label> _page_indicator;

    std::unique_ptr<uitk::lvgl_cpp::Container> _content_card;
    std::unique_ptr<uitk::lvgl_cpp::Label> _line1;
    std::unique_ptr<uitk::lvgl_cpp::Label> _line2;
    std::unique_ptr<uitk::lvgl_cpp::Label> _line3;
    std::unique_ptr<uitk::lvgl_cpp::Label> _line4;
    std::unique_ptr<uitk::lvgl_cpp::Label> _line5;

    int _current_page = 0;          // 0: Overview, 1: Compute, 2: Data/Billing
    int _current_project_index = 0; // 0: All Fleet, 1..N: Specific Project
};

} // namespace gcp_monitor_view

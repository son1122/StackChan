/*
 * SPDX-FileCopyrightText: 2026 M5Stack Technology CO LTD
 *
 * SPDX-License-Identifier: MIT
 */
#include "gcp_monitor_view.h"
#include <cstdio>

namespace gcp_monitor_view {

using namespace uitk::lvgl_cpp;
using namespace gcp_monitor;

GcpMonitorView::GcpMonitorView()
    : _current_page(0), _current_project_index(0)
{
}

GcpMonitorView::~GcpMonitorView()
{
    clearCards();
    _root.reset();
}

void GcpMonitorView::clearCards()
{
    _line1.reset();
    _line2.reset();
    _line3.reset();
    _line4.reset();
    _line5.reset();
    _content_card.reset();
}

void GcpMonitorView::init()
{
    // Screen container (320x240)
    _root = std::make_unique<Container>(lv_screen_active());
    _root->setSize(320, 240);
    _root->setAlign(LV_ALIGN_CENTER);
    _root->setBgColor(lv_color_hex(0x0F172A)); // Dark Slate
    _root->setPadding(0, 0, 0, 0);
    _root->setBorderWidth(0);
    _root->setRadius(0);
    _root->removeFlag(LV_OBJ_FLAG_SCROLLABLE);

    // Header bar (Height 36px)
    _header = std::make_unique<Container>(*_root);
    _header->setSize(320, 36);
    _header->align(LV_ALIGN_TOP_MID, 0, 0);
    _header->setBgColor(lv_color_hex(0x1E293B));
    _header->setBorderWidth(0);
    _header->setRadius(0);
    _header->setPadding(6, 6, 12, 12);
    _header->removeFlag(LV_OBJ_FLAG_SCROLLABLE);

    _title_label = std::make_unique<Label>(*_header);
    _title_label->setText("[ALL FLEET]");
    _title_label->setTextFont(&lv_font_montserrat_14);
    _title_label->setTextColor(lv_color_hex(0x38BDF8)); // Sky Blue
    _title_label->align(LV_ALIGN_LEFT_MID, 4, 0);

    _status_badge = std::make_unique<Label>(*_header);
    _status_badge->setText("HEALTHY");
    _status_badge->setTextFont(&lv_font_montserrat_14);
    _status_badge->setTextColor(lv_color_hex(0x22C55E)); // Green
    _status_badge->align(LV_ALIGN_CENTER, 15, 0);

    _page_indicator = std::make_unique<Label>(*_header);
    _page_indicator->setText("1/3 >");
    _page_indicator->setTextFont(&lv_font_montserrat_14);
    _page_indicator->setTextColor(lv_color_hex(0x94A3B8));
    _page_indicator->align(LV_ALIGN_RIGHT_MID, -4, 0);
}

void GcpMonitorView::nextPage()
{
    _current_page = (_current_page + 1) % 3;
}

void GcpMonitorView::prevPage()
{
    _current_page = (_current_page - 1 + 3) % 3;
}

void GcpMonitorView::nextProject(int total_projects)
{
    if (total_projects <= 0) {
        _current_project_index = 0;
        return;
    }
    // Total selectable targets = 1 (Fleet) + total_projects
    int total_targets = 1 + total_projects;
    _current_project_index = (_current_project_index + 1) % total_targets;
    _current_page = 0; // Reset to page 0 when switching project
}

void GcpMonitorView::prevProject(int total_projects)
{
    if (total_projects <= 0) {
        _current_project_index = 0;
        return;
    }
    int total_targets = 1 + total_projects;
    _current_project_index = (_current_project_index - 1 + total_targets) % total_targets;
    _current_page = 0;
}

void GcpMonitorView::update(const GcpTelemetry& data)
{
    if (!_root) return;

    // 1. Determine Title & Status Badge based on current selected target
    if (_current_project_index == 0 || data.projects.empty()) {
        _title_label->setText("[ALL FLEET]");
        if (data.overall_status == "ok") {
            _status_badge->setText("HEALTHY");
            _status_badge->setTextColor(lv_color_hex(0x22C55E));
        } else if (data.overall_status == "warning") {
            _status_badge->setText("WARN");
            _status_badge->setTextColor(lv_color_hex(0xF59E0B));
        } else {
            _status_badge->setText("ALERT");
            _status_badge->setTextColor(lv_color_hex(0xEF4444));
        }
    } else {
        int p_idx = (_current_project_index - 1) % data.projects.size();
        const auto& proj = data.projects[p_idx];
        std::string title = "[" + proj.project_id + "]";
        if (title.length() > 14) {
            title = title.substr(0, 13) + "..]";
        }
        _title_label->setText(title.c_str());

        if (proj.status == "ok") {
            _status_badge->setText("OK");
            _status_badge->setTextColor(lv_color_hex(0x22C55E));
        } else if (proj.status == "warning") {
            _status_badge->setText("WARN");
            _status_badge->setTextColor(lv_color_hex(0xF59E0B));
        } else {
            _status_badge->setText("ALERT");
            _status_badge->setTextColor(lv_color_hex(0xEF4444));
        }
    }

    char page_str[32];
    snprintf(page_str, sizeof(page_str), "P%d/3 >", (_current_page % 3) + 1);
    _page_indicator->setText(page_str);

    renderPage(data);
}

void GcpMonitorView::renderPage(const GcpTelemetry& data)
{
    clearCards();

    // Content card (Width: 304, Height: 180, Y: 42)
    _content_card = std::make_unique<Container>(*_root);
    _content_card->setSize(304, 180);
    _content_card->align(LV_ALIGN_TOP_MID, 0, 42);
    _content_card->setBgColor(lv_color_hex(0x1E293B));
    _content_card->setRadius(12);
    _content_card->setBorderWidth(1);
    _content_card->setBorderColor(lv_color_hex(0x334155));
    _content_card->setPadding(10, 10, 12, 12);
    _content_card->setFlexFlow(LV_FLEX_FLOW_COLUMN);
    _content_card->setFlexAlign(LV_FLEX_ALIGN_SPACE_BETWEEN, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER);
    _content_card->removeFlag(LV_OBJ_FLAG_SCROLLABLE);

    char buf[128];

    // MODE A: ALL FLEET
    if (_current_project_index == 0 || data.projects.empty()) {
        if (_current_page == 0) {
            // Page 1: Multi-Project Matrix
            _line1 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "PROJECT MATRIX (%d Projects)", (int)data.projects.size());
            _line1->setText(buf);
            _line1->setTextFont(&lv_font_montserrat_14);
            _line1->setTextColor(lv_color_hex(0x38BDF8));

            _line2 = std::make_unique<Label>(*_content_card);
            if (data.projects.size() > 0) {
                snprintf(buf, sizeof(buf), "1. %s: %dP | $%.0f",
                    data.projects[0].project_id.c_str(),
                    data.projects[0].pods_running,
                    data.projects[0].billing_mtd);
            } else {
                snprintf(buf, sizeof(buf), "Total Cost: $%.2f MTD", data.billing.mtd_usd);
            }
            _line2->setText(buf);
            _line2->setTextFont(&lv_font_montserrat_14);
            _line2->setTextColor(lv_color_hex(0xF8FAFC));

            _line3 = std::make_unique<Label>(*_content_card);
            if (data.projects.size() > 1) {
                snprintf(buf, sizeof(buf), "2. %s: %dP | $%.0f",
                    data.projects[1].project_id.c_str(),
                    data.projects[1].pods_running,
                    data.projects[1].billing_mtd);
            } else {
                snprintf(buf, sizeof(buf), "Pods: %d | VMs: %d", data.gke.pods_running, data.vm.instances_running);
            }
            _line3->setText(buf);
            _line3->setTextFont(&lv_font_montserrat_14);
            _line3->setTextColor(lv_color_hex(0xF8FAFC));

            _line4 = std::make_unique<Label>(*_content_card);
            if (data.projects.size() > 2) {
                snprintf(buf, sizeof(buf), "3. %s: %dP | $%.0f",
                    data.projects[2].project_id.c_str(),
                    data.projects[2].pods_running,
                    data.projects[2].billing_mtd);
            } else {
                snprintf(buf, sizeof(buf), "Cloud Run: %d | SQL: %d", data.cloud_run.services_count, data.cloud_sql.instances_up);
            }
            _line4->setText(buf);
            _line4->setTextFont(&lv_font_montserrat_14);
            _line4->setTextColor(lv_color_hex(0xF8FAFC));

            _line5 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "Fleet: $%.2f MTD | %d Alerts", data.billing.mtd_usd, data.incident_count);
            _line5->setText(buf);
            _line5->setTextFont(&lv_font_montserrat_14);
            _line5->setTextColor(lv_color_hex(0x22C55E));

        } else if (_current_page == 1) {
            // Page 2: Fleet Compute
            _line1 = std::make_unique<Label>(*_content_card);
            _line1->setText("FLEET COMPUTE AGGREGATE");
            _line1->setTextFont(&lv_font_montserrat_14);
            _line1->setTextColor(lv_color_hex(0x94A3B8));

            _line2 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "GKE: %d Pods (%d Nodes)", data.gke.pods_running, data.gke.nodes_up);
            _line2->setText(buf);
            _line2->setTextFont(&lv_font_montserrat_14);
            _line2->setTextColor(lv_color_hex(0xF8FAFC));

            _line3 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "VM Instances: %d Running", data.vm.instances_running);
            _line3->setText(buf);
            _line3->setTextFont(&lv_font_montserrat_14);
            _line3->setTextColor(lv_color_hex(0xF8FAFC));

            _line4 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "Cloud Run: %d Svcs (%.1f rps)", data.cloud_run.services_count, data.cloud_run.req_per_sec);
            _line4->setText(buf);
            _line4->setTextFont(&lv_font_montserrat_14);
            _line4->setTextColor(lv_color_hex(0xE2E8F0));

            _line5 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "Cloud SQL: %d DBs (%d Conns)", data.cloud_sql.instances_up, data.cloud_sql.connections);
            _line5->setText(buf);
            _line5->setTextFont(&lv_font_montserrat_14);
            _line5->setTextColor(lv_color_hex(0xE2E8F0));

        } else {
            // Page 3: Fleet Finance & BigQuery
            _line1 = std::make_unique<Label>(*_content_card);
            _line1->setText("FLEET BILLING & BIGQUERY");
            _line1->setTextFont(&lv_font_montserrat_14);
            _line1->setTextColor(lv_color_hex(0x94A3B8));

            _line2 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "$%.2f MTD", data.billing.mtd_usd);
            _line2->setText(buf);
            _line2->setTextFont(&lv_font_montserrat_24);
            _line2->setTextColor(lv_color_hex(0xF8FAFC));

            _line3 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "Today: $%.2f | Budget: %.1f%%", data.billing.today_usd, data.billing.budget_pct);
            _line3->setText(buf);
            _line3->setTextFont(&lv_font_montserrat_14);
            _line3->setTextColor(lv_color_hex(0x38BDF8));

            _line4 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "BigQuery Slots: %d Active", data.bigquery.slot_usage);
            _line4->setText(buf);
            _line4->setTextFont(&lv_font_montserrat_14);
            _line4->setTextColor(lv_color_hex(0xE2E8F0));

            _line5 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "Billed Today: %.1f GB", data.bigquery.today_gb_billed);
            _line5->setText(buf);
            _line5->setTextFont(&lv_font_montserrat_14);
            _line5->setTextColor(lv_color_hex(0xE2E8F0));
        }

    // MODE B: SPECIFIC PROJECT
    } else {
        int p_idx = (_current_project_index - 1) % data.projects.size();
        const auto& proj = data.projects[p_idx];

        if (_current_page == 0) {
            _line1 = std::make_unique<Label>(*_content_card);
            _line1->setText("PROJECT OVERVIEW");
            _line1->setTextFont(&lv_font_montserrat_14);
            _line1->setTextColor(lv_color_hex(0x38BDF8));

            _line2 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "$%.2f MTD", proj.billing_mtd);
            _line2->setText(buf);
            _line2->setTextFont(&lv_font_montserrat_24);
            _line2->setTextColor(lv_color_hex(0xF8FAFC));

            _line3 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "GKE Pods: %d Running", proj.pods_running);
            _line3->setText(buf);
            _line3->setTextFont(&lv_font_montserrat_14);
            _line3->setTextColor(lv_color_hex(0xE2E8F0));

            _line4 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "VM Instances: %d Up", proj.vms_running);
            _line4->setText(buf);
            _line4->setTextFont(&lv_font_montserrat_14);
            _line4->setTextColor(lv_color_hex(0xE2E8F0));

            _line5 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "Alerts: %d Active | Status: %s", proj.incident_count, proj.status.c_str());
            _line5->setText(buf);
            _line5->setTextFont(&lv_font_montserrat_14);
            _line5->setTextColor(proj.status == "ok" ? lv_color_hex(0x22C55E) : lv_color_hex(0xF59E0B));

        } else if (_current_page == 1) {
            _line1 = std::make_unique<Label>(*_content_card);
            _line1->setText("PROJECT WORKLOAD");
            _line1->setTextFont(&lv_font_montserrat_14);
            _line1->setTextColor(lv_color_hex(0x94A3B8));

            _line2 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "Target: %s", proj.project_id.c_str());
            _line2->setText(buf);
            _line2->setTextFont(&lv_font_montserrat_14);
            _line2->setTextColor(lv_color_hex(0xF8FAFC));

            _line3 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "Pods Running: %d", proj.pods_running);
            _line3->setText(buf);
            _line3->setTextFont(&lv_font_montserrat_14);
            _line3->setTextColor(lv_color_hex(0x38BDF8));

            _line4 = std::make_unique<Label>(*_content_card);
            snprintf(buf, sizeof(buf), "VM Instances: %d", proj.vms_running);
            _line4->setText(buf);
            _line4->setTextFont(&lv_font_montserrat_14);
            _line4->setTextColor(lv_color_hex(0xE2E8F0));

            _line5 = std::make_unique<Label>(*_content_card);
            _line5->setText("Tap Head to Switch Project");
            _line5->setTextFont(&lv_font_montserrat_14);
            _line5->setTextColor(lv_color_hex(0x64748B));

        } else {
            _line1 = std::make_unique<Label>(*_content_card);
            _line1->setText("NAVIGATION GUIDE");
            _line1->setTextFont(&lv_font_montserrat_14);
            _line1->setTextColor(lv_color_hex(0x94A3B8));

            _line2 = std::make_unique<Label>(*_content_card);
            _line2->setText("Tap Head: Next Project");
            _line2->setTextFont(&lv_font_montserrat_14);
            _line2->setTextColor(lv_color_hex(0xF8FAFC));

            _line3 = std::make_unique<Label>(*_content_card);
            _line3->setText("Long Press Head: Force Refresh");
            _line3->setTextFont(&lv_font_montserrat_14);
            _line3->setTextColor(lv_color_hex(0x38BDF8));

            _line4 = std::make_unique<Label>(*_content_card);
            _line4->setText("Tap Left/Right: Switch Page");
            _line4->setTextFont(&lv_font_montserrat_14);
            _line4->setTextColor(lv_color_hex(0xE2E8F0));

            _line5 = std::make_unique<Label>(*_content_card);
            _line5->setText("Bottom Bar: Return Home");
            _line5->setTextFont(&lv_font_montserrat_14);
            _line5->setTextColor(lv_color_hex(0x64748B));
        }
    }
}

} // namespace gcp_monitor_view

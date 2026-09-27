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
    : _current_page(0)
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
    // Screen container
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
    _title_label->setText("Google Cloud");
    _title_label->setTextFont(&lv_font_montserrat_14);
    _title_label->setTextColor(lv_color_hex(0x38BDF8)); // Sky Blue
    _title_label->align(LV_ALIGN_LEFT_MID, 4, 0);

    _status_badge = std::make_unique<Label>(*_header);
    _status_badge->setText("OK");
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

void GcpMonitorView::update(const GcpTelemetry& data)
{
    if (!_root) return;

    // Update Status Badge
    if (data.overall_status == "ok") {
        _status_badge->setText("HEALTHY");
        _status_badge->setTextColor(lv_color_hex(0x22C55E)); // Green
    } else if (data.overall_status == "warning") {
        _status_badge->setText("WARN");
        _status_badge->setTextColor(lv_color_hex(0xF59E0B)); // Amber
    } else {
        _status_badge->setText("ALERT");
        _status_badge->setTextColor(lv_color_hex(0xEF4444)); // Red
    }

    char page_str[16];
    snprintf(page_str, sizeof(page_str), "%d/3 >", _current_page + 1);
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
    _content_card->setPadding(12, 12, 14, 14);
    _content_card->setFlexFlow(LV_FLEX_FLOW_COLUMN);
    _content_card->setFlexAlign(LV_FLEX_ALIGN_SPACE_BETWEEN, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER);
    _content_card->removeFlag(LV_OBJ_FLAG_SCROLLABLE);

    char buf[128];

    if (_current_page == 0) {
        // Page 1: Overview & Cloud Billing
        _line1 = std::make_unique<Label>(*_content_card);
        _line1->setText("MONTH-TO-DATE COST");
        _line1->setTextFont(&lv_font_montserrat_14);
        _line1->setTextColor(lv_color_hex(0x94A3B8));

        _line2 = std::make_unique<Label>(*_content_card);
        snprintf(buf, sizeof(buf), "$%.2f", data.billing.mtd_usd);
        _line2->setText(buf);
        _line2->setTextFont(&lv_font_montserrat_24);
        _line2->setTextColor(lv_color_hex(0xF8FAFC));

        _line3 = std::make_unique<Label>(*_content_card);
        snprintf(buf, sizeof(buf), "Today: $%.2f  |  Budget: %.1f%%", data.billing.today_usd, data.billing.budget_pct);
        _line3->setText(buf);
        _line3->setTextFont(&lv_font_montserrat_14);
        _line3->setTextColor(lv_color_hex(0x38BDF8));

        _line4 = std::make_unique<Label>(*_content_card);
        snprintf(buf, sizeof(buf), "GKE: %d Nodes  |  VMs: %d Up", data.gke.nodes_up, data.vm.instances_running);
        _line4->setText(buf);
        _line4->setTextFont(&lv_font_montserrat_14);
        _line4->setTextColor(lv_color_hex(0xE2E8F0));

        _line5 = std::make_unique<Label>(*_content_card);
        snprintf(buf, sizeof(buf), "Run: %d Svcs  |  SQL: %d Up", data.cloud_run.services_count, data.cloud_sql.instances_up);
        _line5->setText(buf);
        _line5->setTextFont(&lv_font_montserrat_14);
        _line5->setTextColor(lv_color_hex(0xE2E8F0));

    } else if (_current_page == 1) {
        // Page 2: Compute & Containers (GKE, VMs, Cloud Run)
        _line1 = std::make_unique<Label>(*_content_card);
        _line1->setText("COMPUTE & CONTAINERS");
        _line1->setTextFont(&lv_font_montserrat_14);
        _line1->setTextColor(lv_color_hex(0x94A3B8));

        _line2 = std::make_unique<Label>(*_content_card);
        snprintf(buf, sizeof(buf), "GKE: %d Pods (Fail: %d)", data.gke.pods_running, data.gke.pods_failed);
        _line2->setText(buf);
        _line2->setTextFont(&lv_font_montserrat_16);
        _line2->setTextColor(data.gke.pods_failed > 0 ? lv_color_hex(0xEF4444) : lv_color_hex(0x34D399));

        _line3 = std::make_unique<Label>(*_content_card);
        snprintf(buf, sizeof(buf), "GKE Load: CPU %.1f%% | RAM %.1f%%", data.gke.cpu_pct, data.gke.ram_pct);
        _line3->setText(buf);
        _line3->setTextFont(&lv_font_montserrat_14);
        _line3->setTextColor(lv_color_hex(0xE2E8F0));

        _line4 = std::make_unique<Label>(*_content_card);
        snprintf(buf, sizeof(buf), "VM Instances: %d (CPU %.1f%%)", data.vm.instances_running, data.vm.avg_cpu_pct);
        _line4->setText(buf);
        _line4->setTextFont(&lv_font_montserrat_14);
        _line4->setTextColor(lv_color_hex(0xE2E8F0));

        _line5 = std::make_unique<Label>(*_content_card);
        snprintf(buf, sizeof(buf), "Cloud Run: %.1f req/s (5xx: %.1f%%)", data.cloud_run.req_per_sec, data.cloud_run.error_5xx_rate);
        _line5->setText(buf);
        _line5->setTextFont(&lv_font_montserrat_14);
        _line5->setTextColor(lv_color_hex(0x38BDF8));

    } else {
        // Page 3: Data & Analytics (Cloud SQL, BigQuery)
        _line1 = std::make_unique<Label>(*_content_card);
        _line1->setText("DATA & ANALYTICS");
        _line1->setTextFont(&lv_font_montserrat_14);
        _line1->setTextColor(lv_color_hex(0x94A3B8));

        _line2 = std::make_unique<Label>(*_content_card);
        snprintf(buf, sizeof(buf), "Cloud SQL: %d DBs Active", data.cloud_sql.instances_up);
        _line2->setText(buf);
        _line2->setTextFont(&lv_font_montserrat_16);
        _line2->setTextColor(lv_color_hex(0x38BDF8));

        _line3 = std::make_unique<Label>(*_content_card);
        snprintf(buf, sizeof(buf), "SQL Usage: CPU %.1f%% | Disk %.1f%%", data.cloud_sql.cpu_pct, data.cloud_sql.storage_pct);
        _line3->setText(buf);
        _line3->setTextFont(&lv_font_montserrat_14);
        _line3->setTextColor(lv_color_hex(0xE2E8F0));

        _line4 = std::make_unique<Label>(*_content_card);
        snprintf(buf, sizeof(buf), "BigQuery Slots: %d Active", data.bigquery.slot_usage);
        _line4->setText(buf);
        _line4->setTextFont(&lv_font_montserrat_14);
        _line4->setTextColor(lv_color_hex(0xE2E8F0));

        _line5 = std::make_unique<Label>(*_content_card);
        snprintf(buf, sizeof(buf), "BQ Today: %.1f GB | %d Errors", data.bigquery.today_gb_billed, data.bigquery.failed_queries_24h);
        _line5->setText(buf);
        _line5->setTextFont(&lv_font_montserrat_14);
        _line5->setTextColor(lv_color_hex(0xA7F3D0));
    }
}

} // namespace gcp_monitor_view

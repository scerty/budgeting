from django.core.exceptions import ValidationError

from .models import ReportColumnType


def build_report_column_specs(template):
    """Compile a validated template into source specifications for a report worker."""
    columns = list(template.columns.select_related(
        "scenario_version",
        "variance_base_column",
        "variance_compare_column",
        "fiscal_period",
        "mixed_cutover_period",
    ).order_by("sort_order", "id"))
    specs = []
    column_ids = {column.id for column in columns}

    for column in columns:
        if column.data_type == ReportColumnType.ACTUALS:
            source = {
                "kind": "actuals",
                "scenario_version_id": None,
                "fiscal_period_id": column.fiscal_period_id,
                "mixed_cutover_period_id": None,
            }
        elif column.data_type == ReportColumnType.SCENARIO:
            source = {
                "kind": "scenario",
                "scenario_version_id": column.scenario_version_id,
                "fiscal_period_id": column.fiscal_period_id,
                "mixed_cutover_period_id": None,
            }
        elif column.data_type == ReportColumnType.MIXED:
            source = {
                "kind": "mixed",
                "scenario_version_id": column.scenario_version_id,
                "fiscal_period_id": column.fiscal_period_id,
                "mixed_cutover_period_id": column.mixed_cutover_period_id,
            }
        elif column.data_type == ReportColumnType.VARIANCE:
            if (
                column.variance_base_column_id not in column_ids
                or column.variance_compare_column_id not in column_ids
            ):
                raise ValidationError("Variance columns must reference columns in the same template.")
            source = {
                "kind": "variance",
                "scenario_version_id": None,
                "fiscal_period_id": column.fiscal_period_id,
                "mixed_cutover_period_id": None,
                "base_column_id": column.variance_base_column_id,
                "compare_column_id": column.variance_compare_column_id,
                "as_percentage": column.variance_as_percentage,
            }
        else:
            raise ValidationError(f"Unsupported report column type: {column.data_type}")

        specs.append(
            {
                "column_id": column.id,
                "label": column.label,
                "sort_order": column.sort_order,
                "period_from_offset": column.period_from_offset,
                "period_to_offset": column.period_to_offset,
                "prior_year": column.prior_year,
                "source": source,
            }
        )

    return specs

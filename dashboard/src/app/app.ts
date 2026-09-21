import { DecimalPipe } from '@angular/common';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { finalize, forkJoin } from 'rxjs';

interface CubeResponse<T> {
  data: T[];
}

interface CubeQuery {
  measures: string[];
  dimensions: string[];
  order: Record<string, string>;
  filters?: Array<{
    member: string;
    operator: string;
    values: string[];
  }>;
}

interface BranchRow {
  'ExpensesByBranch.branchCode': string;
  'ExpensesByBranch.branchName': string;
  'ExpensesByBranch.city': string;
  'ExpensesByBranch.totalExpenses': string;
  'ExpensesByBranch.expenseCount': string;
}

interface MonthRow {
  'ExpensesByBranchMonth.monthKey': string;
  'ExpensesByBranchMonth.year': string;
  'ExpensesByBranchMonth.monthName': string;
  'ExpensesByBranchMonth.totalExpenses': string;
  'ExpensesByBranchMonth.expenseCount': string;
}

interface BudgetVsActualRow {
  'BudgetVsActual.organizationCode': string;
  'BudgetVsActual.organizationName': string;
  'BudgetVsActual.fiscalPeriodCode': string;
  'BudgetVsActual.fiscalPeriodName': string;
  'BudgetVsActual.fiscalYear': string;
  'BudgetVsActual.legalEntityCode': string;
  'BudgetVsActual.groupAccountCode': string;
  'BudgetVsActual.groupAccountName': string;
  'BudgetVsActual.branchCode': string;
  'BudgetVsActual.branchName': string;
  'BudgetVsActual.departmentCode': string;
  'BudgetVsActual.currencyCode': string;
  'BudgetVsActual.budgetAmount': string;
  'BudgetVsActual.actualAmount': string;
  'BudgetVsActual.varianceAmount': string;
}

interface MonthlyBudgetVsActualRow {
  'BudgetVsActualMonth.organizationCode': string;
  'BudgetVsActualMonth.organizationName': string;
  'BudgetVsActualMonth.fiscalPeriodCode': string;
  'BudgetVsActualMonth.fiscalPeriodName': string;
  'BudgetVsActualMonth.fiscalYear': string;
  'BudgetVsActualMonth.monthKey': string;
  'BudgetVsActualMonth.monthYear': string;
  'BudgetVsActualMonth.monthName': string;
  'BudgetVsActualMonth.groupAccountCode': string;
  'BudgetVsActualMonth.groupAccountName': string;
  'BudgetVsActualMonth.legalEntityCode': string;
  'BudgetVsActualMonth.legalEntityName': string;
  'BudgetVsActualMonth.branchCode': string;
  'BudgetVsActualMonth.branchName': string;
  'BudgetVsActualMonth.departmentCode': string;
  'BudgetVsActualMonth.departmentName': string;
  'BudgetVsActualMonth.currencyCode': string;
  'BudgetVsActualMonth.budgetAmount': string;
  'BudgetVsActualMonth.actualAmount': string;
  'BudgetVsActualMonth.varianceAmount': string;
}

interface MonthlyGroupSection {
  key: string;
  groupAccountCode: string;
  groupAccountName: string;
  organizationCode: string;
  organizationName: string;
  fiscalPeriodCode: string;
  fiscalPeriodName: string;
  fiscalYear: string;
  legalEntityCode: string;
  legalEntityName: string;
  branchCode: string;
  branchName: string;
  departmentCode: string;
  departmentName: string;
  currencyCode: string;
  rows: MonthlyBudgetVsActualRow[];
  budgetAmount: number;
  actualAmount: number;
  varianceAmount: number;
}

interface PlanningRow {
  'Planning.organizationCode': string;
  'Planning.organizationName': string;
  'Planning.scenarioCode': string;
  'Planning.scenarioName': string;
  'Planning.scenarioVersionCode': string;
  'Planning.scenarioVersionName': string;
  'Planning.fiscalPeriodCode': string;
  'Planning.fiscalPeriodName': string;
  'Planning.fiscalYear': string;
  'Planning.legalEntityCode': string;
  'Planning.groupAccountCode': string;
  'Planning.groupAccountName': string;
  'Planning.branchCode': string;
  'Planning.branchName': string;
  'Planning.departmentCode': string;
  'Planning.currencyCode': string;
  'Planning.plannedAmount': string;
  'Planning.planningFactCount': string;
}

@Component({
  selector: 'app-root',
  imports: [DecimalPipe],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  private readonly http = inject(HttpClient);
  private readonly cubeUrl = '/cubejs-api/v1/load';

  protected readonly allBranchRows = signal<BranchRow[]>([]);
  protected readonly branchRows = signal<BranchRow[]>([]);
  protected readonly monthRows = signal<MonthRow[]>([]);
  protected readonly allBudgetRows = signal<BudgetVsActualRow[]>([]);
  protected readonly allPlanningRows = signal<PlanningRow[]>([]);
  protected readonly budgetRows = signal<BudgetVsActualRow[]>([]);
  protected readonly planningRows = signal<PlanningRow[]>([]);
  protected readonly monthlyGroupRows = signal<MonthlyBudgetVsActualRow[]>([]);
  protected readonly monthlyBranchRows = signal<MonthlyBudgetVsActualRow[]>([]);
  protected readonly selectedOrganization = signal('all');
  protected readonly selectedPeriod = signal('all');
  protected readonly selectedScenarioVersion = signal('all');
  protected readonly selectedBranch = signal('all');
  protected readonly selectedMonthlyGroupAccount = signal('all');
  protected readonly selectedMonthlyLegalEntity = signal('all');
  protected readonly selectedMonthlyDepartment = signal('all');
  protected readonly selectedMonthlyCurrency = signal('all');
  protected readonly isLoading = signal(true);
  protected readonly errorMessage = signal('');

  protected readonly branchOptions = computed(() => [
    { code: 'all', label: 'All branches' },
    ...this.allBranchRows().map((row) => ({
      code: row['ExpensesByBranch.branchCode'],
      label: row['ExpensesByBranch.branchName']
    }))
  ]);

  protected readonly organizationOptions = computed(() => {
    const options = new Map<string, string>();
    [...this.allBudgetRows(), ...this.allPlanningRows()].forEach((row) => {
      const code = 'BudgetVsActual.organizationCode' in row
        ? row['BudgetVsActual.organizationCode']
        : row['Planning.organizationCode'];
      const name = 'BudgetVsActual.organizationName' in row
        ? row['BudgetVsActual.organizationName']
        : row['Planning.organizationName'];
      if (code) {
        options.set(code, name || code);
      }
    });
    return [
      { code: 'all', label: 'All organizations' },
      ...Array.from(options, ([code, label]) => ({ code, label }))
    ];
  });

  protected readonly periodOptions = computed(() => {
    const options = new Map<string, string>();
    [...this.allBudgetRows(), ...this.allPlanningRows()].forEach((row) => {
      const code = 'BudgetVsActual.fiscalPeriodCode' in row
        ? row['BudgetVsActual.fiscalPeriodCode']
        : row['Planning.fiscalPeriodCode'];
      const name = 'BudgetVsActual.fiscalPeriodName' in row
        ? row['BudgetVsActual.fiscalPeriodName']
        : row['Planning.fiscalPeriodName'];
      const year = 'BudgetVsActual.fiscalYear' in row
        ? row['BudgetVsActual.fiscalYear']
        : row['Planning.fiscalYear'];
      if (code) {
        options.set(code, `${name || code} · ${year}`);
      }
    });
    return [
      { code: 'all', label: 'All periods' },
      ...Array.from(options, ([code, label]) => ({ code, label }))
    ];
  });

  protected readonly scenarioVersionOptions = computed(() => {
    const options = new Map<string, string>();
    this.allPlanningRows().forEach((row) => {
      const code = row['Planning.scenarioVersionCode'];
      if (code) {
        options.set(
          code,
          `${row['Planning.scenarioName']} · ${row['Planning.scenarioVersionName'] || code}`
        );
      }
    });
    return [
      { code: 'all', label: 'All scenario versions' },
      ...Array.from(options, ([code, label]) => ({ code, label }))
    ];
  });

  protected readonly monthlyGroupAccountOptions = computed(() => {
    const options = new Map<string, string>();
    this.monthlyGroupRows().forEach((row) => {
      const code = row['BudgetVsActualMonth.groupAccountCode'];
      const name = row['BudgetVsActualMonth.groupAccountName'];
      if (code) {
        options.set(code, `${code} · ${name || code}`);
      }
    });
    return [
      { code: 'all', label: 'All group accounts' },
      ...Array.from(options, ([code, label]) => ({ code, label }))
    ];
  });

  protected readonly monthlyLegalEntityOptions = computed(() => {
    const options = new Map<string, string>();
    this.monthlyGroupRows().forEach((row) => {
      const code = row['BudgetVsActualMonth.legalEntityCode'];
      const name = row['BudgetVsActualMonth.legalEntityName'];
      if (code) {
        options.set(code, `${code} · ${name || code}`);
      }
    });
    return [
      { code: 'all', label: 'All legal entities' },
      ...Array.from(options, ([code, label]) => ({ code, label }))
    ];
  });

  protected readonly monthlyDepartmentOptions = computed(() => {
    const options = new Map<string, string>();
    this.monthlyGroupRows().forEach((row) => {
      const code = row['BudgetVsActualMonth.departmentCode'];
      const name = row['BudgetVsActualMonth.departmentName'];
      if (code) {
        options.set(code, `${code} · ${name || code}`);
      }
    });
    return [
      { code: 'all', label: 'All departments' },
      ...Array.from(options, ([code, label]) => ({ code, label }))
    ];
  });

  protected readonly monthlyCurrencyOptions = computed(() => {
    const currencies = new Set(
      this.monthlyGroupRows()
        .map((row) => row['BudgetVsActualMonth.currencyCode'])
        .filter(Boolean)
    );
    return [
      { code: 'all', label: 'All currencies' },
      ...Array.from(currencies, (code) => ({ code, label: code }))
    ];
  });

  protected readonly filteredMonthlyGroupRows = computed(() => {
    const groupAccount = this.selectedMonthlyGroupAccount();
    const legalEntity = this.selectedMonthlyLegalEntity();
    const department = this.selectedMonthlyDepartment();
    const currency = this.selectedMonthlyCurrency();

    return this.monthlyGroupRows().filter((row) =>
      (groupAccount === 'all' || row['BudgetVsActualMonth.groupAccountCode'] === groupAccount)
      && (legalEntity === 'all' || row['BudgetVsActualMonth.legalEntityCode'] === legalEntity)
      && (department === 'all' || row['BudgetVsActualMonth.departmentCode'] === department)
      && (currency === 'all' || row['BudgetVsActualMonth.currencyCode'] === currency)
    );
  });

  protected readonly monthlyGroupSections = computed<MonthlyGroupSection[]>(() => {
    const sections = new Map<string, MonthlyGroupSection>();

    this.filteredMonthlyGroupRows().forEach((row) => {
      const key = [
        row['BudgetVsActualMonth.organizationCode'],
        row['BudgetVsActualMonth.fiscalPeriodCode'],
        row['BudgetVsActualMonth.groupAccountCode'],
        row['BudgetVsActualMonth.legalEntityCode'],
        row['BudgetVsActualMonth.branchCode'],
        row['BudgetVsActualMonth.departmentCode'],
        row['BudgetVsActualMonth.currencyCode']
      ].join('|');
      const existing = sections.get(key);

      if (existing) {
        existing.rows.push(row);
        existing.budgetAmount += Number(row['BudgetVsActualMonth.budgetAmount']);
        existing.actualAmount += Number(row['BudgetVsActualMonth.actualAmount']);
        existing.varianceAmount += Number(row['BudgetVsActualMonth.varianceAmount']);
        return;
      }

      sections.set(key, {
        key,
        groupAccountCode: row['BudgetVsActualMonth.groupAccountCode'],
        groupAccountName: row['BudgetVsActualMonth.groupAccountName'],
        organizationCode: row['BudgetVsActualMonth.organizationCode'],
        organizationName: row['BudgetVsActualMonth.organizationName'],
        fiscalPeriodCode: row['BudgetVsActualMonth.fiscalPeriodCode'],
        fiscalPeriodName: row['BudgetVsActualMonth.fiscalPeriodName'],
        fiscalYear: row['BudgetVsActualMonth.fiscalYear'],
        legalEntityCode: row['BudgetVsActualMonth.legalEntityCode'],
        legalEntityName: row['BudgetVsActualMonth.legalEntityName'],
        branchCode: row['BudgetVsActualMonth.branchCode'],
        branchName: row['BudgetVsActualMonth.branchName'],
        departmentCode: row['BudgetVsActualMonth.departmentCode'],
        departmentName: row['BudgetVsActualMonth.departmentName'],
        currencyCode: row['BudgetVsActualMonth.currencyCode'],
        rows: [row],
        budgetAmount: Number(row['BudgetVsActualMonth.budgetAmount']),
        actualAmount: Number(row['BudgetVsActualMonth.actualAmount']),
        varianceAmount: Number(row['BudgetVsActualMonth.varianceAmount'])
      });
    });

    return Array.from(sections.values());
  });

  protected readonly peakMonthTotal = computed(() =>
    Math.max(
      1,
      ...this.monthRows().map((row) =>
        Number(row['ExpensesByBranchMonth.totalExpenses'])
      )
    )
  );

  protected readonly totalBudget = computed(() =>
    this.budgetRows().reduce(
      (total, row) => total + Number(row['BudgetVsActual.budgetAmount']),
      0
    )
  );

  protected readonly totalActual = computed(() =>
    this.budgetRows().reduce(
      (total, row) => total + Number(row['BudgetVsActual.actualAmount']),
      0
    )
  );

  protected readonly totalVariance = computed(() =>
    this.budgetRows().reduce(
      (total, row) => total + Number(row['BudgetVsActual.varianceAmount']),
      0
    )
  );

  protected readonly totalPlanned = computed(() =>
    this.planningRows().reduce(
      (total, row) => total + Number(row['Planning.plannedAmount']),
      0
    )
  );

  constructor() {
    this.loadDashboard();
  }

  protected loadDashboard(): void {
    this.isLoading.set(true);
    this.errorMessage.set('');

    const branchQuery: CubeQuery = {
      measures: [
        'ExpensesByBranch.totalExpenses',
        'ExpensesByBranch.expenseCount'
      ],
      dimensions: [
        'ExpensesByBranch.branchCode',
        'ExpensesByBranch.branchName',
        'ExpensesByBranch.city'
      ],
      order: { 'ExpensesByBranch.branchCode': 'asc' }
    };

    const selectedBranch = this.selectedBranch();
    if (selectedBranch !== 'all') {
      branchQuery.filters = [{
        member: 'ExpensesByBranch.branchCode',
        operator: 'equals',
        values: [selectedBranch]
      }];
    }

    const monthQuery: CubeQuery = {
      measures: [
        'ExpensesByBranchMonth.totalExpenses',
        'ExpensesByBranchMonth.expenseCount'
      ],
      dimensions: [
        'ExpensesByBranchMonth.monthKey',
        'ExpensesByBranchMonth.year',
        'ExpensesByBranchMonth.monthName'
      ],
      order: { 'ExpensesByBranchMonth.monthKey': 'asc' }
    };

    if (selectedBranch !== 'all') {
      monthQuery.filters = [{
        member: 'ExpensesByBranchMonth.branchCode',
        operator: 'equals',
        values: [selectedBranch]
      }];
    }

    const budgetQuery: CubeQuery = {
      measures: [
        'BudgetVsActual.budgetAmount',
        'BudgetVsActual.actualAmount',
        'BudgetVsActual.varianceAmount'
      ],
      dimensions: [
        'BudgetVsActual.organizationCode',
        'BudgetVsActual.organizationName',
        'BudgetVsActual.fiscalPeriodCode',
        'BudgetVsActual.fiscalPeriodName',
        'BudgetVsActual.fiscalYear',
        'BudgetVsActual.legalEntityCode',
        'BudgetVsActual.groupAccountCode',
        'BudgetVsActual.groupAccountName',
        'BudgetVsActual.branchCode',
        'BudgetVsActual.branchName',
        'BudgetVsActual.departmentCode',
        'BudgetVsActual.currencyCode'
      ],
      order: { 'BudgetVsActual.fiscalPeriodCode': 'asc' }
    };

    const planningQuery: CubeQuery = {
      measures: [
        'Planning.plannedAmount',
        'Planning.planningFactCount'
      ],
      dimensions: [
        'Planning.organizationCode',
        'Planning.organizationName',
        'Planning.scenarioCode',
        'Planning.scenarioName',
        'Planning.scenarioVersionCode',
        'Planning.scenarioVersionName',
        'Planning.fiscalPeriodCode',
        'Planning.fiscalPeriodName',
        'Planning.fiscalYear',
        'Planning.legalEntityCode',
        'Planning.groupAccountCode',
        'Planning.groupAccountName',
        'Planning.branchCode',
        'Planning.branchName',
        'Planning.departmentCode',
        'Planning.currencyCode'
      ],
      order: { 'Planning.fiscalPeriodCode': 'asc' }
    };

    const monthlyGroupQuery: CubeQuery = {
      measures: [
        'BudgetVsActualMonth.budgetAmount',
        'BudgetVsActualMonth.actualAmount',
        'BudgetVsActualMonth.varianceAmount'
      ],
      dimensions: [
        'BudgetVsActualMonth.organizationCode',
        'BudgetVsActualMonth.organizationName',
        'BudgetVsActualMonth.fiscalPeriodCode',
        'BudgetVsActualMonth.fiscalPeriodName',
        'BudgetVsActualMonth.fiscalYear',
        'BudgetVsActualMonth.monthKey',
        'BudgetVsActualMonth.monthYear',
        'BudgetVsActualMonth.monthName',
        'BudgetVsActualMonth.groupAccountCode',
        'BudgetVsActualMonth.groupAccountName',
        'BudgetVsActualMonth.legalEntityCode',
        'BudgetVsActualMonth.legalEntityName',
        'BudgetVsActualMonth.branchCode',
        'BudgetVsActualMonth.branchName',
        'BudgetVsActualMonth.departmentCode',
        'BudgetVsActualMonth.departmentName',
        'BudgetVsActualMonth.currencyCode'
      ],
      order: {
        'BudgetVsActualMonth.monthKey': 'asc',
        'BudgetVsActualMonth.groupAccountCode': 'asc',
        'BudgetVsActualMonth.legalEntityCode': 'asc',
        'BudgetVsActualMonth.branchCode': 'asc',
        'BudgetVsActualMonth.departmentCode': 'asc'
      }
    };

    const monthlyBranchQuery: CubeQuery = {
      measures: [
        'BudgetVsActualMonth.budgetAmount',
        'BudgetVsActualMonth.actualAmount',
        'BudgetVsActualMonth.varianceAmount'
      ],
      dimensions: [
        'BudgetVsActualMonth.monthKey',
        'BudgetVsActualMonth.monthYear',
        'BudgetVsActualMonth.monthName',
        'BudgetVsActualMonth.branchCode',
        'BudgetVsActualMonth.branchName',
        'BudgetVsActualMonth.currencyCode'
      ],
      order: {
        'BudgetVsActualMonth.monthKey': 'asc',
        'BudgetVsActualMonth.branchCode': 'asc'
      }
    };

    this.applyContextFilters(budgetQuery, 'BudgetVsActual');
    this.applyContextFilters(planningQuery, 'Planning', true);
    this.applyContextFilters(monthlyGroupQuery, 'BudgetVsActualMonth');
    this.applyContextFilters(monthlyBranchQuery, 'BudgetVsActualMonth');

    forkJoin({
      branches: this.http.get<CubeResponse<BranchRow>>(this.cubeUrl, {
        params: new HttpParams().set('query', JSON.stringify(branchQuery))
      }),
      months: this.http.get<CubeResponse<MonthRow>>(this.cubeUrl, {
        params: new HttpParams().set('query', JSON.stringify(monthQuery))
      }),
      budget: this.http.get<CubeResponse<BudgetVsActualRow>>(this.cubeUrl, {
        params: new HttpParams().set('query', JSON.stringify(budgetQuery))
      }),
      planning: this.http.get<CubeResponse<PlanningRow>>(this.cubeUrl, {
        params: new HttpParams().set('query', JSON.stringify(planningQuery))
      }),
      monthlyGroup: this.http.get<CubeResponse<MonthlyBudgetVsActualRow>>(this.cubeUrl, {
        params: new HttpParams().set('query', JSON.stringify(monthlyGroupQuery))
      }),
      monthlyBranch: this.http.get<CubeResponse<MonthlyBudgetVsActualRow>>(this.cubeUrl, {
        params: new HttpParams().set('query', JSON.stringify(monthlyBranchQuery))
      })
    })
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: ({ branches, months, budget, planning, monthlyGroup, monthlyBranch }) => {
          this.branchRows.set(branches.data);
          if (selectedBranch === 'all') {
            this.allBranchRows.set(branches.data);
          }
          this.monthRows.set(months.data);
          this.budgetRows.set(budget.data);
          this.planningRows.set(planning.data);
          this.monthlyGroupRows.set(monthlyGroup.data);
          this.monthlyBranchRows.set(monthlyBranch.data);
          if (this.allBudgetRows().length === 0) {
            this.allBudgetRows.set(budget.data);
          }
          if (this.allPlanningRows().length === 0) {
            this.allPlanningRows.set(planning.data);
          }
        },
        error: () => {
          this.errorMessage.set(
            'Could not reach Cube.js. Check that the Cube service is running.'
          );
        }
      });
  }

  protected selectBranch(code: string): void {
    this.selectedBranch.set(code);
    this.loadDashboard();
  }

  protected selectOrganization(code: string): void {
    this.selectedOrganization.set(code);
    this.loadDashboard();
  }

  protected selectPeriod(code: string): void {
    this.selectedPeriod.set(code);
    this.loadDashboard();
  }

  protected selectScenarioVersion(code: string): void {
    this.selectedScenarioVersion.set(code);
    this.loadDashboard();
  }

  protected selectMonthlyGroupAccount(code: string): void {
    this.selectedMonthlyGroupAccount.set(code);
  }

  protected selectMonthlyLegalEntity(code: string): void {
    this.selectedMonthlyLegalEntity.set(code);
  }

  protected selectMonthlyDepartment(code: string): void {
    this.selectedMonthlyDepartment.set(code);
  }

  protected selectMonthlyCurrency(code: string): void {
    this.selectedMonthlyCurrency.set(code);
  }

  protected resetMonthlyFilters(): void {
    this.selectedMonthlyGroupAccount.set('all');
    this.selectedMonthlyLegalEntity.set('all');
    this.selectedMonthlyDepartment.set('all');
    this.selectedMonthlyCurrency.set('all');
  }

  protected asNumber(value: string): number {
    return Number(value);
  }

  protected barWidth(value: string): string {
    return `${(Number(value) / this.peakMonthTotal()) * 100}%`;
  }

  private applyContextFilters(
    query: CubeQuery,
    cube: string,
    includeScenarioVersion = false
  ): void {
    const filters: NonNullable<CubeQuery['filters']> = [];
    const organization = this.selectedOrganization();
    const period = this.selectedPeriod();
    const branch = this.selectedBranch();
    const scenarioVersion = this.selectedScenarioVersion();

    if (organization !== 'all') {
      filters.push({
        member: `${cube}.organizationCode`,
        operator: 'equals',
        values: [organization]
      });
    }
    if (period !== 'all') {
      filters.push({
        member: `${cube}.fiscalPeriodCode`,
        operator: 'equals',
        values: [period]
      });
    }
    if (branch !== 'all') {
      filters.push({
        member: `${cube}.branchCode`,
        operator: 'equals',
        values: [branch]
      });
    }
    if (includeScenarioVersion && scenarioVersion !== 'all') {
      filters.push({
        member: `${cube}.scenarioVersionCode`,
        operator: 'equals',
        values: [scenarioVersion]
      });
    }
    if (filters.length > 0) {
      query.filters = filters;
    }
  }
}

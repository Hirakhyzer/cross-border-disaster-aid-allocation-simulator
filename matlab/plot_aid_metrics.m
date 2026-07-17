function plot_aid_metrics(outputDir)
%PLOT_AID_METRICS Plot synthetic aid allocation metrics after Python run.
%   plot_aid_metrics('outputs') reads generated CSV files and saves a figure.

if nargin < 1
    outputDir = 'outputs';
end
coveragePath = fullfile(outputDir, 'results', 'synthetic_region_coverage.csv');
fairnessPath = fullfile(outputDir, 'results', 'synthetic_fairness_audit.csv');
figDir = fullfile(outputDir, 'figures');
if ~exist(figDir, 'dir')
    mkdir(figDir);
end
coverage = readtable(coveragePath);
fairness = readtable(fairnessPath);
figure('Name', 'Synthetic Aid Allocation Metrics');
tiledlayout(1,2);
nexttile;
bar(categorical(coverage.region_id), coverage.coverage_ratio);
title('Region coverage');
ylabel('Coverage ratio');
xtickangle(70);
nexttile;
bar(categorical(fairness.country), fairness.country_coverage_ratio);
title('Country coverage');
ylabel('Coverage ratio');
exportgraphics(gcf, fullfile(figDir, 'matlab_aid_metrics.png'), 'Resolution', 180);
end

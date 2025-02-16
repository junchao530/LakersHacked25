#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <string.h>

#define PI 3.14159265358979323846

// Box-Muller transform to generate a normally distributed random number
double rand_normal(double mean, double std) {
    static int haveSpare = 0;
    static double spare;
    
    if (haveSpare) {
        haveSpare = 0;
        return mean + std * spare;
    }
    
    haveSpare = 1;
    double u, v, s;
    do {
        u = (rand() / (double)RAND_MAX) * 2.0 - 1.0;
        v = (rand() / (double)RAND_MAX) * 2.0 - 1.0;
        s = u * u + v * v;
    } while (s >= 1.0 || s == 0.0);
    
    s = sqrt(-2.0 * log(s) / s);
    spare = v * s;
    return mean + std * (u * s);
}

// Determine seasonal factor based on month
double get_seasonal_factor(int month) {
    if (month == 5 || month == 6 || month == 7)
        return 1.2;
    if (month == 11 || month == 0 || month == 1)
        return 0.9;
    return 1.0;
}

// Return weekend factor
double get_weekend_factor(int wday) {
    return (wday == 0 || wday == 6) ? 0.95 : 1.0;
}

// Calculate water purity
double get_water_purity(time_t current_time, time_t start_time) {
    const long long seven_months_seconds = 7 * 30.44 * 24 * 3600;
    long long elapsed_seconds = (long long)difftime(current_time, start_time);
    long long cycle_time = elapsed_seconds % seven_months_seconds;
    return 95.0 - (30.0 * (cycle_time / (double)seven_months_seconds));
}

int main() {
    srand(42);
    FILE *fp = fopen("simulated_water_flow_3_years.csv", "w");
    if (fp == NULL) {
        perror("Error opening file");
        return 1;
    }

    fprintf(fp, "timestamp,flow_rate,day_type,month,temperature,purity\n");

    double baseline = 5.0;
    double amplitude = 5.0;
    double noise_std_flow = 1.0;
    double noise_std_temp = 1.0;

    // Get today's date and time
    time_t now = time(NULL);
    struct tm *today_tm = localtime(&now);

    // Set end_time to today
    struct tm end_tm = *today_tm;
    time_t end_time = mktime(&end_tm);

    // Set start_time to 3 years before today
    struct tm start_tm = *today_tm;
    start_tm.tm_year -= 3; // Subtract 3 years
    time_t start_time = mktime(&start_tm);

    // Total minutes in the 3-year range
    long long total_minutes = (long long)difftime(end_time, start_time) / 60 + 1;

    char timestamp_str[25];
    struct tm *current_tm;
    time_t current_time = start_time;
    long long counter = 0;
    long long progress_interval = total_minutes / 100;

    while (current_time <= end_time) {
        current_tm = localtime(&current_time);
        strftime(timestamp_str, sizeof(timestamp_str), "%Y-%m-%d:%H:%M", current_tm);

        double hour_fraction = current_tm->tm_hour + current_tm->tm_min / 60.0;
        double daily_pattern = sin(2 * PI * (hour_fraction / 24.0)) +
                               0.5 * sin(2 * PI * ((hour_fraction - 8.0) / 24.0));
        double seasonal_factor = get_seasonal_factor(current_tm->tm_mon);
        double weekend_factor = get_weekend_factor(current_tm->tm_wday);
        double noise_flow = rand_normal(0.0, noise_std_flow);
        double noise_temp = rand_normal(0.0, noise_std_temp);
        double flow_rate = baseline + amplitude * daily_pattern * seasonal_factor * weekend_factor + noise_flow;
        if (flow_rate < 0) flow_rate = 0;
        double temperature = 20.0 + (((current_tm->tm_mon + 1) - 6) * 5) + noise_temp;
        char *day_type = (current_tm->tm_wday == 0 || current_tm->tm_wday == 6) ? "Weekend" : "Weekday";
        double purity = get_water_purity(current_time, start_time);
        
        fprintf(fp, "%s,%.3f,%s,%d,%.2f,%.2f\n", timestamp_str, flow_rate, day_type, current_tm->tm_mon + 1, temperature, purity);
        current_time += 60; // Increment by 1 minute
        counter++;

        if (counter % progress_interval == 0) {
            printf("Progress: %.0f%%\n", (counter / (double)total_minutes) * 100);
        }
    }

    fclose(fp);
    printf("Data generation complete! Output written to simulated_water_flow_3_years.csv\n");

    return 0;
}
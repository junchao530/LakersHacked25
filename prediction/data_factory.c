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

// Determine seasonal factor based on month (tm_mon is 0-indexed: 0=Jan, ..., 11=Dec)
double get_seasonal_factor(int month) {
    // Summer: June (5), July (6), August (7)
    if (month == 5 || month == 6 || month == 7)
        return 1.2;
    // Winter: December (11), January (0), February (1)
    if (month == 11 || month == 0 || month == 1)
        return 0.9;
    return 1.0;
}

// Return weekend factor: if day is Saturday (6) or Sunday (0) then 0.95, else 1.0.
double get_weekend_factor(int wday) {
    if (wday == 0 || wday == 6)
        return 0.95;
    return 1.0;
}

int main() {
    // Seed the random number generator
    srand(42);

    // Open the CSV file for writing
    FILE *fp = fopen("simulated_water_flow_3_years.csv", "w");
    if (fp == NULL) {
        perror("Error opening file");
        return 1;
    }

    // Write CSV header
    fprintf(fp, "timestamp,flow_rate,day_type,month,temperature\n");

    // Define simulation parameters
    double baseline = 5.0;    // L/min
    double amplitude = 5.0;   // amplitude for daily variation
    double noise_std_flow = 1.0;  // standard deviation for flow noise
    double noise_std_temp = 1.0;  // standard deviation for temperature noise

    // Set start and end dates using struct tm
    struct tm start_tm = {0};
    start_tm.tm_year = 2020 - 1900;
    start_tm.tm_mon = 0;    // January
    start_tm.tm_mday = 1;
    start_tm.tm_hour = 0;
    start_tm.tm_min = 0;
    start_tm.tm_sec = 0;
    time_t start_time = mktime(&start_tm);

    struct tm end_tm = {0};
    end_tm.tm_year = 2022 - 1900;
    end_tm.tm_mon = 11;     // December
    end_tm.tm_mday = 31;
    end_tm.tm_hour = 23;
    end_tm.tm_min = 59;
    end_tm.tm_sec = 59;
    time_t end_time = mktime(&end_tm);

    // Total seconds to iterate (could be around 94-95 million seconds)
    long long total_seconds = (long long)difftime(end_time, start_time) + 1;

    char timestamp_str[25];
    struct tm *current_tm;
    time_t current_time = start_time;

    // For progress output
    long long counter = 0;
    long long progress_interval = total_seconds / 100; // update every 1%

    // Iterate over every second in the range
    while (current_time <= end_time) {
        current_tm = localtime(&current_time);
        
        // Format timestamp as "yyyy-mm-dd:HH:MM:SS"
        strftime(timestamp_str, sizeof(timestamp_str), "%Y-%m-%d:%H:%M:%S", current_tm);
        
        // Compute fractional hour (hour + minute/60 + second/3600)
        double hour_fraction = current_tm->tm_hour + current_tm->tm_min / 60.0 + current_tm->tm_sec / 3600.0;
        
        // Daily pattern: two sine waves to simulate peaks
        double daily_pattern = sin(2 * PI * (hour_fraction / 24.0)) +
                               0.5 * sin(2 * PI * ((hour_fraction - 8.0) / 24.0));
        
        // Seasonal factor based on month (tm_mon: 0=Jan, ..., 11=Dec)
        double seasonal_factor = get_seasonal_factor(current_tm->tm_mon);
        
        // Weekend factor based on day of week (tm_wday: 0=Sun, ..., 6=Sat)
        double weekend_factor = get_weekend_factor(current_tm->tm_wday);
        
        // Generate random noise for flow rate and temperature
        double noise_flow = rand_normal(0.0, noise_std_flow);
        double noise_temp = rand_normal(0.0, noise_std_temp);
        
        // Calculate flow rate (L/min) and ensure non-negative
        double flow_rate = baseline + amplitude * daily_pattern * seasonal_factor * weekend_factor + noise_flow;
        if (flow_rate < 0) flow_rate = 0;
        
        // Calculate temperature.
        // For example: base 20°C, modified by month (tm_mon + 1) relative to 6 plus noise.
        double temperature = 20.0 + (((current_tm->tm_mon + 1) - 6) * 5) + noise_temp;
        
        // Determine day type: "Weekend" if Sunday (0) or Saturday (6)
        char *day_type = (current_tm->tm_wday == 0 || current_tm->tm_wday == 6) ? "Weekend" : "Weekday";
        
        // Write the record to the CSV file
        // Columns: timestamp, flow_rate, day_type, month (1-12), temperature
        fprintf(fp, "%s,%.3f,%s,%d,%.2f\n", timestamp_str, flow_rate, day_type, current_tm->tm_mon + 1, temperature);

        // Increment the time by 1 second
        current_time++;
        counter++;
        
        // Optionally print progress every 1%
        if (counter % progress_interval == 0) {
            printf("Progress: %.0f%%\n", (counter / (double)total_seconds) * 100);
        }
    }

    fclose(fp);
    printf("Data generation complete! Output written to simulated_water_flow_3_years.csv\n");

    return 0;
}

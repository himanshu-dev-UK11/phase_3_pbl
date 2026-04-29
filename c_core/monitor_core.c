typedef struct LeakResult {
    int score;
    int leak;
} LeakResult;

static double clamp_score(double score) {
    if (score < 0.0) {
        return 0.0;
    }
    if (score > 100.0) {
        return 100.0;
    }
    return score;
}

__declspec(dllexport) int calculate_leak(
    double memory_mb,
    double cpu_percent,
    double threshold_mb,
    double memory_percent,
    double model_score,
    LeakResult *result
) {
    double score = model_score;

    if (result == 0) {
        return 0;
    }

    if (memory_mb > threshold_mb) {
        score += 20.0;
    }
    if (memory_percent >= 85.0) {
        score += 15.0;
    }
    if (cpu_percent >= 90.0) {
        score += 10.0;
    }

    result->score = (int)clamp_score(score);
    result->leak = result->score >= 60 || memory_mb > threshold_mb;
    return 1;
}

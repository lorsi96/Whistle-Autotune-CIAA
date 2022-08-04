
#include "sapi.h"
#include "arm_math.h"
#include "arm_const_structs.h"
#include "tone_frequencies.h"

#define MAX_TONES_N 120
#define SAMPLING_FREQUENCY_HZ 8000
#define ZERO_PADDING_SAMPS 128

#define BATCH_SAMPLES_N 128

typedef struct {
    arm_rfft_instance_q15 S;
    int16_t signal[BATCH_SAMPLES_N];
    q15_t fft_real_cmplx[2 * BATCH_SAMPLES_N];
    q15_t fft_mag_real[BATCH_SAMPLES_N / 2 + 1];
    q15_t fft_max_value;
    uint32_t fft_max_ind;
} PSFSignal_t;

void PSFSignal_compute(PSFSignal_t* self) {
    arm_rfft_init_q15(&self->S, BATCH_SAMPLES_N, /*ifftFlag=*/0, /*bitRev=*/1);
    arm_rfft_q15(&self->S, self->signal, self->fft_real_cmplx);
    arm_cmplx_mag_squared_q15(self->fft_real_cmplx, self->fft_mag_real,
                              BATCH_SAMPLES_N / 2 + 1);
    arm_max_q15(self->fft_mag_real, BATCH_SAMPLES_N / 2 + 1,
                &self->fft_max_value, &self->fft_max_ind);
}

/**
 * @brief
 *
 * @param freq_hz
 * @param tunes_hz
 * @param tunes_sz
 */
float psf_closest_tune(float freq_hz, float* tunes_hz, uint32_t tunes_sz) {
    static float diff_vector[MAX_TONES_N];
    float res;
    uint32_t ind;
    arm_offset_f32(tunes_hz, -freq_hz, diff_vector, tunes_sz);
    arm_abs_f32(diff_vector, diff_vector, tunes_sz);
    arm_min_f32(diff_vector, tunes_sz, &res, &ind);
    return tunes_hz[ind];
}

struct header_struct {
    char pre[4];
    uint32_t id;
    uint16_t N;
    uint16_t fs;
    uint32_t maxIndex;  // indexador de maxima energia por cada fft
    q15_t maxValue;     // maximo valor de energia del bin por cada fft
    float matchedTone;
    char pos[4];
} __attribute__((packed));

struct header_struct header = {.pre = "head",
                               .id = 0,
                               .N = 128,
                               .fs = SAMPLING_FREQUENCY_HZ,
                               .maxIndex = 0,
                               .maxValue = 0,
                               .matchedTone = 0.0,
                               .pos = "tail"};

void psf_fft(q15_t* signalTimeSamps, q15_t* outBuff, uint32_t size) {
    static arm_rfft_instance_q15 S;
    static q15_t fftRealComplex[1024];
    arm_rfft_init_q15(&S, size, /*ifftFlagR=*/0, /*bitReverseFlag=*/1);
    arm_rfft_q15(&S, signalTimeSamps, fftRealComplex);
    arm_cmplx_mag_squared_q15(fftRealComplex, outBuff, size);
}

void psf_get_main_freq_component(q15_t* timeSignalSamples, uint32_t size,
                                 q15_t* maxValue, uint32_t* maxIndex) {
    static q15_t realFftBuffer[1024];
    psf_fft(timeSignalSamples, realFftBuffer, size);
    arm_max_q15(realFftBuffer, size / 2 + 1, maxValue, maxIndex);
}

void psf_hardware_init() {
    boardConfig();
    uartConfig(UART_USB, 460800);
    adcConfig(ADC_ENABLE);
    // dacConfig(DAC_ENABLE);
    cyclesCounterInit(EDU_CIAA_NXP_CLOCK_SPEED);
}

int main(void) {
    uint16_t sample = 0;
    PSFSignal_t ciaa_signal;
    uint16_t* adc = ciaa_signal.signal;
    psf_hardware_init();
    while(true) {
      cyclesCounterReset();
      adc[sample] = (((int16_t)adcRead(CH1) - 512) << 6); 
      if (++sample == header.N) {
        sample = 0;
        PSFSignal_compute(&ciaa_signal);
        header.maxValue = ciaa_signal.fft_max_value;
        header.maxIndex = ciaa_signal.fft_max_ind;
        header.matchedTone =
        psf_closest_tune(header.maxIndex * 62.857, C_MAJOR_SCALE,
                             sizeof(C_MAJOR_SCALE) / sizeof(C_MAJOR_SCALE[0]));
        header.id++;
        uartWriteByteArray(UART_USB, (uint8_t*)&header,
                           sizeof(struct header_struct));
        adcRead(CH1);
      }
      while (cyclesCounterRead() < EDU_CIAA_NXP_CLOCK_SPEED / SAMPLING_FREQUENCY_HZ);   
    }
}

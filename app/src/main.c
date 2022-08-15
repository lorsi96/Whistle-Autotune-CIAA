/**
 * @file main.c
 * @author Lucas Orsi (lorsi@itba.edu.ar)
 * @brief Whistle tone detector application.
 * @version 0.1
 * @date 2022-08-15
 * 
 * @copyright Copyright (c) 2022 
 */

/* ************************************************************************* */
/*                             Public Inclusions                             */
/* ************************************************************************* */
#include "sapi.h"
#include "arm_math.h"
#include "arm_const_structs.h"
#include "tone_frequencies.h"

/* ************************************************************************* */
/*                              Public constants                             */
/* ************************************************************************* */
#define TARGET_SCALE  C_MAJOR_SCALE
#define MAX_TONES_N (sizeof(TARGET_SCALE) / sizeof(TARGET_SCALE[0]))

#define PSF_BAUDRATE  460800
#define SAMPLING_FREQUENCY_HZ 8000.0
#define BATCH_SAMPLES_N 512
#define PADDING_SAMPLES_N  0
#define TOTAL_SAMPLES_N  (BATCH_SAMPLES_N + PADDING_SAMPLES_N)

#define RESOLUTION_HZ  (SAMPLING_FREQUENCY_HZ / TOTAL_SAMPLES_N)

/* ************************************************************************* */
/*                                 Data Types                                */
/* ************************************************************************* */
typedef struct {
    arm_rfft_instance_q15 S;
    int16_t signal[TOTAL_SAMPLES_N];
    q15_t fft_real_cmplx[2 * TOTAL_SAMPLES_N];
    q15_t fft_mag_real[TOTAL_SAMPLES_N / 2 + 1];
    q15_t fft_max_value;
    uint32_t fft_max_ind;
} PSFSignal_t;

typedef struct {
    char pre[4];
    uint32_t id;        //!< Packet Id.
    uint16_t N;         //!< Batch size.
    uint16_t fs;        //!< Sampling frequency.
    uint32_t maxIndex;  //!< Highest energy FFT Bin index.
    q15_t maxValue;     //!< Highest energy FFT Bin value.
    float matchedTone;  //!< Matched frequency of the given tonal scale.
    uint32_t toneIndex; //!< Index of matched frequency in tonal scale array.
    char pos[4];
} __attribute__((packed)) PSF_DataPacket_t;

/* ************************************************************************* */
/*                                 Functions                                 */
/* ************************************************************************* */

/* ************************** PSF Signal Functions ************************* */

/**
 * @brief Computes all fields of a given PSFSignal_t
 * @details This includes complex & real fft, plus the latters max val and ind.
 * @param[inout] self 
 */
void PSFSignal_update(PSFSignal_t* self) {
    arm_rfft_init_q15(&self->S, TOTAL_SAMPLES_N, /*ifftFlag=*/0, /*bitRev=*/1);
    arm_rfft_q15(&self->S, self->signal, self->fft_real_cmplx);
    arm_cmplx_mag_squared_q15(self->fft_real_cmplx, self->fft_mag_real,
                              TOTAL_SAMPLES_N / 2 + 1);
    arm_max_q15(self->fft_mag_real, TOTAL_SAMPLES_N / 2 + 1,
                &self->fft_max_value, &self->fft_max_ind);
}

/* ******************************** PSF Lib ******************************** */

/**
 * @brief Given a frequency values, finds the tune that's closest to it in a 
 *        given tonal scale.
 * 
 * @param[in] freq_hz frequency to be matched to a scale.
 * @param[in] tunes_hz list with frequencies belonging to a tonal scale.
 * @param[in] tunes_sz size of tunes_hz list.
 * @param[out] tone_index index of the matched tone in the tunes_hz list.   
 * @return float  mateched frequency.
 */
float PSFLib_closestTune(float freq_hz, float* tunes_hz, uint32_t tunes_sz, uint32_t* tone_index) {
    static float diff_vector[MAX_TONES_N];
    float res;
    uint32_t ind;
    arm_offset_f32(tunes_hz, -freq_hz, diff_vector, tunes_sz);
    arm_abs_f32(diff_vector, diff_vector, tunes_sz);
    arm_min_f32(diff_vector, tunes_sz, &res, &ind);
    *tone_index = ind;
    return tunes_hz[ind];
}

/**
 * @brief Hardware initialization function.
 * @details Includes board, uart and ADC configuration.
 * 
 */
void PSFLib_hardwareInit() {
    boardConfig();
    uartConfig(UART_USB, 460800);
    adcConfig(ADC_ENABLE);
    // dacConfig(DAC_ENABLE);
    cyclesCounterInit(EDU_CIAA_NXP_CLOCK_SPEED);
}

/**
 * @brief Acces header global instance.
 * 
 * @return PSF_DataPacket_t* global packet reference.
 */
PSF_DataPacket_t* PSFLib_getPacketHeader() {
    static PSF_DataPacket_t header = {
        .pre = "head",
        .id = 0,
        .N = BATCH_SAMPLES_N,
        .fs = SAMPLING_FREQUENCY_HZ,
        .maxIndex = 0,
        .maxValue = 0,
        .matchedTone = 0.0,
        .pos = "tail"
    };
    return &header;
}

/* ************************************************************************* */
/*                              Main Application                             */
/* ************************************************************************* */

int main(void) {
    uint16_t sample = 0;
    PSFSignal_t ciaa_signal;
    uint32_t idx;
    PSFLib_hardwareInit();
    PSF_DataPacket_t* header = PSFLib_getPacketHeader();
    while(true) {
      cyclesCounterReset();
      ciaa_signal.signal[sample++] = (((int16_t)adcRead(CH1) - 512) << 6); 
      if(sample > header->N) sample = 0;
      if (sample == (header->N / 16)) {
        PSFSignal_update(&ciaa_signal);
        header->maxValue = ciaa_signal.fft_max_value;
        header->maxIndex = ciaa_signal.fft_max_ind;
        header->matchedTone =
        PSFLib_closestTune(header->maxIndex * RESOLUTION_HZ, TARGET_SCALE,
                             MAX_TONES_N, &idx);
        header->toneIndex = idx;
        header->id++;
        uartWriteByteArray(UART_USB, (uint8_t*)header, sizeof(PSF_DataPacket_t));
        adcRead(CH1);
      }
      while (cyclesCounterRead() < EDU_CIAA_NXP_CLOCK_SPEED / SAMPLING_FREQUENCY_HZ);   
    }
}

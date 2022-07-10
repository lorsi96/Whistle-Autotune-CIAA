#include "sapi.h"
#include "arm_math.h"
#include "arm_const_structs.h"
#include "tone_frequencies.h"

#define MAX_TONES_N  120
#define BITS 10						// cantidad de bits usado para cuantizar
uint32_t tick	= 0   ;
uint16_t tone	= 100 ;
uint16_t B		= 2500;
uint16_t sweept = 5;

/**
 * @brief 
 * 
 * @param freq_hz 
 * @param tunes_hz 
 * @param tunes_sz 
 */
float psf_closest_tune(float freq_hz, const float *tunes_hz, uint32_t tunes_sz) {
   static float diff_vector[MAX_TONES_N];
   float res; uint32_t ind;
   arm_offset_f32(tunes_hz, -freq_hz, diff_vector, tunes_sz);
   arm_abs_f32(diff_vector, diff_vector, tunes_sz);
   arm_min_f32(diff_vector, tunes_sz, &res, &ind); 
   return tunes_hz[ind];
}


struct header_struct {
   char		pre[4];
   uint32_t id;
   uint16_t N;
   uint16_t fs ;
   uint32_t maxIndex; // indexador de maxima energia por cada fft
   q15_t maxValue;	  // maximo valor de energia del bin por cada fft
   float matchedTone;
   char		pos[4];
} __attribute__ ((packed));

struct header_struct header={"head",0,128,10000,0,0,0.0,"tail"};

int main ( void ) {
   uint16_t sample = 0;
   arm_rfft_instance_q15 S;
   q15_t fftIn [ header.N	   ];// guarda copia de samples en Q15 como in para la fft.La fft corrompe los datos de la entrada!
   q15_t fftOut[ header.N *2   ];	// salida de la fft
   q15_t fftMag[ header.N /2+1 ]; // magnitud de la FFT
   int16_t adc [ header.N	   ];

   boardConfig		 (							);
   uartConfig		 ( UART_USB ,460800			);
   adcConfig		 ( ADC_ENABLE				);
   //dacConfig		 ( DAC_ENABLE				);
   cyclesCounterInit ( EDU_CIAA_NXP_CLOCK_SPEED );

   while(1) {
	  cyclesCounterReset();

	  uartWriteByteArray ( UART_USB ,(uint8_t* )&adc[sample]		,sizeof(adc[0]) );	 // envia el sample ANTERIOR
	  uartWriteByteArray ( UART_USB ,(uint8_t* )&fftOut[sample*2]	,sizeof(fftOut[0])); // envia la fft del sample ANTERIO
	  uartWriteByteArray ( UART_USB ,(uint8_t* )&fftOut[sample*2+1] ,sizeof(fftOut[0])); // envia la fft del sample ANTERIO
	  adc[sample]	= (((int16_t )adcRead(CH1)-512)>>(10-BITS))<<(6+10-BITS);			 // PISA el sample que se acaba de mandar con una nueva muestra
	  fftIn[sample] = adc[sample];														 // copia del adc porque la fft corrompe el arreglo de entrada
	  if ( ++sample==header.N ) {
      gpioToggle ( LEDR );						  // este led blinkea a fs/N
      sample = 0;
      arm_rfft_init_q15		   ( &S		,header.N	  ,0				,1				  ); // inicializa una estructira que usa la funcion fft para procesar los datos. Notar el /2 para el largo
      arm_rfft_q15			   ( &S		,fftIn		  ,fftOut							  ); // por fin.. ejecuta la rfft REAL fft
      arm_cmplx_mag_squared_q15 ( fftOut ,fftMag		  ,header.N/2+1						  );
      arm_max_q15			   ( fftMag ,header.N/2+1 ,&header.maxValue ,&header.maxIndex );
      header.matchedTone = psf_closest_tune(
         header.maxIndex * 10000.0 / header.N, 
         CHROMATIC_SCALE, 
         sizeof(CHROMATIC_SCALE)/sizeof(CHROMATIC_SCALE[0])
      );
      header.id++;
      uartWriteByteArray ( UART_USB ,(uint8_t*)&header ,sizeof(struct header_struct ));

      //		 for(int i=0;i<header.N;i++) {
      //			uartWriteByteArray ( UART_USB ,(uint8_t* )&adc[i]	,sizeof(adc[0]) );	 // envia el sample ANTERIOR
      //			uartWriteByteArray ( UART_USB ,(uint8_t* )&fftOut[i*2] ,sizeof(fftOut[0])); // envia la fft del sample ANTERIO
      //			uartWriteByteArray ( UART_USB ,(uint8_t* )&fftOut[i*2+1] ,sizeof(fftOut[0])); // envia la fft del sample ANTERIO
      //		 }
      adcRead(CH1); //why?? hay algun efecto minimo en el 1er sample.. puede ser por el blinkeo de los leds o algo que me corre 10 puntos el primer sample. Con esto se resuelve.. habria que investigar el problema en detalle
	  }
	  gpioToggle ( LED1 );											 // este led blinkea a fs/2
	  while(cyclesCounterRead()< EDU_CIAA_NXP_CLOCK_SPEED/header.fs) // el clk de la CIAA es 204000000
		 ;
   }
}

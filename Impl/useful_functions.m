
%***************************************************************************
%   Last lab session: experiments
%
%   This file contains useful functions to operate the USRPs: each function
%   is to be inserted at the right location in your own code
%
%%***************************************************************************
% 

% *************************************************************************
% Functions useful for the TX code
% *************************************************************************

%% Configuration of the USRP device as a transmitter
tx = comm.SDRuTransmitter(...
              'Platform', platform , ...                                USRP type (e.g., 'B210')
              'SerialNum', address , ...                                USRP serial number
              'CenterFrequency', fc , ...                               Carrier frequency (range: 70MHz -> 6GHz)
              'ChannelMapping' , 1 , ...                                e.g., 1, 2, or [1 2] 
              'LocalOscillatorOffset' , 20e3 , ...                      Change the IF LO frequency (no influence on the carrier frequency). Cannot be adjusted for MIMO operation (must be [0 0]) (value depends on USRP: TO CHECK)
              'Gain' , g_tx , ...                                       Overall USRP gain in dB. For MIMO with different gain, specify a vector e.g., [g1 g2]
              'PPSSource' , 'Internal', ...                             Parts per second (PPS) signal source (Internal or External)
              'ClockSource' , 'Internal', ...                           10MHz clock signal (Internal or External)
              'MasterClockRate' , fs , ...                              Master clock rate in Hz (i.e., ADC/DAC clock rate). The range is: 5e6 to 56e6              
              'InterpolationFactor' , 1 , ...                           Oversampling ratio applied by the USRP one the signal sent through USB
              'TransportDataType' , 'int16' , ...                       Transport data type per IQ component (int8 or int16). So each complex sample is twice TransportDataType
              'EnableBurstMode' , 0 ...                                 Option to enable or not burst mode (1 or 0 resp.), specified as a numeric or logical value of 1 (true) or 0 (false). To produce a set of contiguous frames without an overrun or underrun to the radio, set this property to 1 (true). Enabling burst mode helps you simulate models that cannot run in real time.
              ) ;               
          
%% Send the TX signal (waveform) to USRP
tx( signal_TX ) ;                                                       % Send data to USRP
% Remark 1: the range of sent data (ie, signal_TX) should be within [-1 1]
% Remark 2: the number of samples transmitted by a frame, ie, the length of 
%   signal_TX should not exceed 30500, otherwise, the upload to the USRP 
%   takes lot of time (but possible)

%% Save variables into a .mat file
save('file_name.mat','variable_1','variable_2','variable_3') ;

% *************************************************************************
% Functions useful for the RX code
% *************************************************************************

%% Load vairables recorded in a .mat file
load('file_name.mat') ;

%% Configuration of the USRP device:
rx = comm.SDRuReceiver(...
              'Platform', platform , ...                                USRP type (e.g., 'B210')
              'SerialNum', address , ...                                USRP serial number
              'CenterFrequency', fc , ...                               Carrier frequency (range: 70MHz -> 6GHz)
              'ChannelMapping' , 1 , ...                                e.g., 1, 2, or [1 2] 
              'LocalOscillatorOffset' , 20e3 , ...                      Change the IF LO frequency (no influence on the carrier frequency). Cannot be adjusted for MIMO operation (must be [0 0]) (value depends on USRP: TO CHECK)
              'Gain' , g_rx , ...                                       Overall USRP gain in dB. For MIMO with different gain, specify a vector e.g., [G1 G2] (value depends on USRP: TO CHECK)
              'PPSSource' , 'Internal', ...                             Parts per second (PPS) signal source (Internal or External)
              'ClockSource' , 'Internal', ...                           10MHz clock signal (Internal or External)              
              'MasterClockRate' , fs , ...                              Master clock rate in Hz (i.e., ADC/DAC clock rate). The range is: 5e6 to 56e6              
              'TransportDataType' , 'int16' , ...                       Transport data type per IQ component (int8 or int16). So each complex sample is twice TransportDataType
              'DecimationFactor' , 1 , ...                              Undersampling ratio applied by the USRP before sending the data through USB (Range: 1 to 128, then only even numbers from 128 to 256 and multiples of 4 from 256 to 512. The radio uses the interpolation factor when it upconverts the complex baseband signal to an intermediate frequency (IF) signal.          )          
              'SamplesPerFrame' , nb_pt_ac , ...                        Default is 362. Ethernet packets have a size of 1500 8-bit bytes.
              'EnableBurstMode' , 0 ...                                 Option to enable or not burst mode (1 or 0 resp.), specified as a numeric or logical value of 1 (true) or 0 (false). To produce a set of contiguous frames without an overrun or underrun to the radio, set this property to 1 (true). Enabling burst mode helps you simulate models that cannot run in real time.
              ) ;               

%% Record and retrieve the RX signal
signal_RX = step( rx ) ;          
signal_RX = double( signal_RX ) ;

%% Coarse time synchronization
% To demodulate the received signal and to compare the received bits to the
% transmitted ones, the starting point of the signal must be first found.
% To do so, we performed here a time sychronization between the TX signal
% and RX signal. Once the RX signal starting sample is found, we crop the
% RX signal to matfche the size of the TX signal (this is of course not the
% way it is done in practice as the receiver cannot a priori know the TX
% signal. In practice, pilot sequences are sent to allow for this time
% synchronization (the pilot sequences are supposed to be a priori known to
% the receiver)
[ signal_RX_sync ] = syncfun ( signal_RX , signal_TX , fs ) ;


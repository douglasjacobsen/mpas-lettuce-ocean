Feature: Bit-Restartable simulations
	MPAS-Ocean simulations are bit-repstartable
	across different decompositions.

	Scenario: 4 vs 16 procs with split explicit - RealWorld
		Given A "QU" "240km" "worldOcean" "split_explicit" test
		Given I perform a 4 processor MPAS "ocean_model_testing" run
		Given I perform a 16 processor MPAS "ocean_model_testing" run with restart
		When I compute the RMS of "temperature"
		When I compute the RMS of "layerThickness"
		Then I see "temperature" RMS of 0
		Then I see "layerThickness" RMS of 0
		Then I clean the test directory

	Scenario: 4 vs 16 procs with RK4 - RealWorld
		Given A "QU" "240km" "worldOcean" "RK4" test
		Given I perform a 4 processor MPAS "ocean_model_testing" run
		Given I perform a 16 processor MPAS "ocean_model_testing" run with restart
		When I compute the RMS of "temperature"
		When I compute the RMS of "layerThickness"
		Then I see "temperature" RMS of 0
		Then I see "layerThickness" RMS of 0
		Then I clean the test directory

	Scenario: 2 vs 16 procs with split explicit
		Given A "10000m" "20levs" "baroclinic_channel" "split_explicit" test
		Given I perform a 2 processor MPAS "ocean_model_testing" run
		Given I perform a 16 processor MPAS "ocean_model_testing" run with restart
		When I compute the RMS of "temperature"
		When I compute the RMS of "layerThickness"
		Then I see "temperature" RMS of 0
		Then I see "layerThickness" RMS of 0
		Then I clean the test directory

	Scenario: 1 vs 24 procs with RK4
		Given A "10000m" "20levs" "baroclinic_channel" "RK4" test
		Given I perform a 1 processor MPAS "ocean_model_testing" run
		Given I perform a 24 processor MPAS "ocean_model_testing" run with restart
		When I compute the RMS of "temperature"
		When I compute the RMS of "layerThickness"
		Then I see "temperature" RMS of 0
		Then I see "layerThickness" RMS of 0
 		Then I clean the test directory

	Scenario: 2 vs 16 procs with split explicit
		Given A "10km" "40layer" "overflow" "split_explicit" test
		Given I perform a 2 processor MPAS "ocean_model_testing" run
		Given I perform a 16 processor MPAS "ocean_model_testing" run with restart
		When I compute the RMS of "temperature"
		When I compute the RMS of "layerThickness"
		Then I see "temperature" RMS of 0
		Then I see "layerThickness" RMS of 0
		Then I clean the test directory

	Scenario: 1 vs 24 procs with RK4
		Given A "10km" "40layer" "overflow" "RK4" test
		Given I perform a 1 processor MPAS "ocean_model_testing" run
		Given I perform a 24 processor MPAS "ocean_model_testing" run with restart
		When I compute the RMS of "temperature"
		When I compute the RMS of "layerThickness"
		Then I see "temperature" RMS of 0
		Then I see "layerThickness" RMS of 0
		#Then I clean the test directory


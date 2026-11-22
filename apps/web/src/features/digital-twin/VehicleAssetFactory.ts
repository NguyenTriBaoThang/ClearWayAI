import * as THREE from 'three';
import { VehicleClass } from '@clearway/shared';

export interface VehicleMeshBundle {
  group: THREE.Group;
  vehicleClass: VehicleClass;
  id: string;
  strobeMaterials?: THREE.MeshBasicMaterial[];
  update?: (timeMs: number) => void;
}

/**
 * VehicleAssetFactory procedurally constructs lightweight, high-fidelity 3D vehicles
 * matching Vietnamese urban mixed traffic and emergency corridor services:
 * - Motorcycle / Scooter (high density urban)
 * - Passenger Sedan / Car
 * - SUV / Crossover
 * - Urban Transit Bus
 * - Delivery Cargo Truck
 * - Emergency Ambulance (with dual alternating red/cyan strobe lightbars)
 * - Emergency Fire Engine (with rescue ladder & quad sirens)
 */
export class VehicleAssetFactory {
  private disposables: { dispose: () => void }[] = [];

  // Shared reusable materials
  private tireMat: THREE.MeshStandardMaterial;
  private rimMat: THREE.MeshStandardMaterial;
  private glassMat: THREE.MeshStandardMaterial;
  private headlightMat: THREE.MeshBasicMaterial;
  private taillightMat: THREE.MeshBasicMaterial;

  constructor() {
    this.tireMat = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.9, metalness: 0.1 });
    this.rimMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.3, metalness: 0.8 });
    this.glassMat = new THREE.MeshStandardMaterial({ color: 0x07152f, roughness: 0.2, metalness: 0.7 });
    this.headlightMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    this.taillightMat = new THREE.MeshBasicMaterial({ color: 0xef476f });

    this.disposables.push(this.tireMat, this.rimMat, this.glassMat, this.headlightMat, this.taillightMat);
  }

  /**
   * 1. Motorcycle / Scooter (Xe máy đô thị)
   */
  public createMotorcycle(id: string, color: number = 0x00e5ff): VehicleMeshBundle {
    const group = new THREE.Group();
    group.name = `Vehicle_Motorcycle_${id}`;

    const bodyMat = new THREE.MeshStandardMaterial({ color, roughness: 0.4, metalness: 0.6 });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x1f2937, roughness: 0.8 });
    this.disposables.push(bodyMat, darkMat);

    // Chassis & Seat
    const bodyGeo = new THREE.BoxGeometry(0.55, 0.45, 1.4);
    const body = new THREE.Mesh(bodyGeo, bodyMat);
    body.position.set(0, 0.55, 0);
    group.add(body);

    const seatGeo = new THREE.BoxGeometry(0.45, 0.2, 0.7);
    const seat = new THREE.Mesh(seatGeo, darkMat);
    seat.position.set(0, 0.75, -0.15);
    group.add(seat);

    // Front & Rear Wheels (Cylinder along X)
    const wheelGeo = new THREE.CylinderGeometry(0.28, 0.28, 0.15, 12);
    wheelGeo.rotateZ(Math.PI / 2);

    const frontWheel = new THREE.Mesh(wheelGeo, this.tireMat);
    frontWheel.position.set(0, 0.28, 0.7);
    group.add(frontWheel);

    const rearWheel = new THREE.Mesh(wheelGeo, this.tireMat);
    rearWheel.position.set(0, 0.28, -0.7);
    group.add(rearWheel);

    // Handlebar & Headlight
    const barGeo = new THREE.BoxGeometry(0.75, 0.08, 0.08);
    const bar = new THREE.Mesh(barGeo, darkMat);
    bar.position.set(0, 0.95, 0.5);
    group.add(bar);

    const lightGeo = new THREE.SphereGeometry(0.1, 8, 8);
    const light = new THREE.Mesh(lightGeo, this.headlightMat);
    light.position.set(0, 0.85, 0.75);
    group.add(light);

    // Stylized Rider Silhouette (Torso + Helmet)
    const torsoGeo = new THREE.BoxGeometry(0.4, 0.5, 0.25);
    const torso = new THREE.Mesh(torsoGeo, darkMat);
    torso.position.set(0, 1.1, -0.05);
    group.add(torso);

    const helmetGeo = new THREE.SphereGeometry(0.18, 12, 12);
    const helmet = new THREE.Mesh(helmetGeo, bodyMat);
    helmet.position.set(0, 1.45, -0.05);
    group.add(helmet);

    this.disposables.push(bodyGeo, seatGeo, wheelGeo, barGeo, lightGeo, torsoGeo, helmetGeo);

    return { group, vehicleClass: 'motorcycle', id };
  }

  /**
   * 2. Passenger Car (Sedan)
   */
  public createPassengerCar(id: string, color: number = 0x38bdf8): VehicleMeshBundle {
    const group = new THREE.Group();
    group.name = `Vehicle_Car_${id}`;

    const bodyMat = new THREE.MeshStandardMaterial({ color, roughness: 0.35, metalness: 0.65 });
    this.disposables.push(bodyMat);

    // Lower Chassis: 1.8m x 0.6m x 4.2m
    const chassisGeo = new THREE.BoxGeometry(1.8, 0.55, 4.2);
    const chassis = new THREE.Mesh(chassisGeo, bodyMat);
    chassis.position.set(0, 0.55, 0);
    group.add(chassis);

    // Cabin Greenhouse: 1.5m x 0.65m x 2.2m
    const cabinGeo = new THREE.BoxGeometry(1.5, 0.6, 2.2);
    const cabin = new THREE.Mesh(cabinGeo, this.glassMat);
    cabin.position.set(0, 1.05, -0.15);
    group.add(cabin);

    // Roof: 1.4m x 0.1m x 2.0m
    const roofGeo = new THREE.BoxGeometry(1.45, 0.08, 1.95);
    const roof = new THREE.Mesh(roofGeo, bodyMat);
    roof.position.set(0, 1.38, -0.15);
    group.add(roof);

    // 4 Wheels
    this.addVehicleWheels(group, 0.9, 0.32, 1.35);

    // Headlights (Front: +Z)
    this.addFrontHeadlights(group, 0.65, 0.55, 2.12);

    // Taillights (Rear: -Z)
    this.addRearTaillights(group, 0.65, 0.6, -2.12);

    this.disposables.push(chassisGeo, cabinGeo, roofGeo);

    return { group, vehicleClass: 'passenger_car', id };
  }

  /**
   * 3. SUV / Urban Crossover
   */
  public createSUV(id: string, color: number = 0x06d6a0): VehicleMeshBundle {
    const group = new THREE.Group();
    group.name = `Vehicle_SUV_${id}`;

    const bodyMat = new THREE.MeshStandardMaterial({ color, roughness: 0.4, metalness: 0.55 });
    this.disposables.push(bodyMat);

    // High Clearance Chassis: 1.95m x 0.7m x 4.6m
    const chassisGeo = new THREE.BoxGeometry(1.95, 0.7, 4.6);
    const chassis = new THREE.Mesh(chassisGeo, bodyMat);
    chassis.position.set(0, 0.7, 0);
    group.add(chassis);

    // Square-back Cabin: 1.65m x 0.75m x 2.8m
    const cabinGeo = new THREE.BoxGeometry(1.65, 0.75, 2.8);
    const cabin = new THREE.Mesh(cabinGeo, this.glassMat);
    cabin.position.set(0, 1.35, -0.3);
    group.add(cabin);

    // Roof Rack Bars
    const rackGeo = new THREE.BoxGeometry(1.4, 0.06, 2.2);
    const rack = new THREE.Mesh(rackGeo, bodyMat);
    rack.position.set(0, 1.75, -0.3);
    group.add(rack);

    // Wheels (Higher radius: 0.38m)
    this.addVehicleWheels(group, 1.0, 0.38, 1.5);

    // Headlights & Taillights
    this.addFrontHeadlights(group, 0.75, 0.75, 2.32);
    this.addRearTaillights(group, 0.75, 0.8, -2.32);

    this.disposables.push(chassisGeo, cabinGeo, rackGeo);

    return { group, vehicleClass: 'suv', id };
  }

  /**
   * 4. Urban Transit Bus (Xe buýt thành phố)
   */
  public createBus(id: string, color: number = 0x00e5ff): VehicleMeshBundle {
    const group = new THREE.Group();
    group.name = `Vehicle_Bus_${id}`;

    const bodyMat = new THREE.MeshStandardMaterial({ color, roughness: 0.45, metalness: 0.4 });
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.5 });
    this.disposables.push(bodyMat, whiteMat);

    // Bus Main Body: 2.5m x 2.8m x 11.2m
    const bodyGeo = new THREE.BoxGeometry(2.5, 2.6, 11.2);
    const body = new THREE.Mesh(bodyGeo, bodyMat);
    body.position.set(0, 1.8, 0);
    group.add(body);

    // Continuous Side Glazing Window Strips
    const windowGeo = new THREE.BoxGeometry(2.55, 0.9, 9.6);
    const windows = new THREE.Mesh(windowGeo, this.glassMat);
    windows.position.set(0, 2.1, -0.2);
    group.add(windows);

    // Front Destination Display Screen
    const signGeo = new THREE.BoxGeometry(1.8, 0.35, 0.1);
    const signMat = new THREE.MeshBasicMaterial({ color: 0xffd166 });
    const sign = new THREE.Mesh(signGeo, signMat);
    sign.position.set(0, 2.8, 5.61);
    group.add(sign);
    this.disposables.push(signGeo, signMat);

    // 6 Heavy Wheels (Front axle + Dual rear axles)
    const wheelGeo = new THREE.CylinderGeometry(0.48, 0.48, 0.3, 14);
    wheelGeo.rotateZ(Math.PI / 2);

    const wheelPositions = [
      { x: 1.25, z: 3.8 },
      { x: -1.25, z: 3.8 },
      { x: 1.25, z: -3.2 },
      { x: -1.25, z: -3.2 },
      { x: 1.25, z: -4.4 },
      { x: -1.25, z: -4.4 },
    ];

    wheelPositions.forEach((pos) => {
      const wheel = new THREE.Mesh(wheelGeo, this.tireMat);
      wheel.position.set(pos.x, 0.48, pos.z);
      group.add(wheel);
    });

    // Front Headlights & Rear Taillights
    this.addFrontHeadlights(group, 0.95, 0.85, 5.62);
    this.addRearTaillights(group, 0.95, 0.95, -5.62);

    this.disposables.push(bodyGeo, windowGeo, wheelGeo);

    return { group, vehicleClass: 'bus', id };
  }

  /**
   * 5. Delivery Cargo Truck (Xe tải chở hàng)
   */
  public createTruck(id: string, color: number = 0xffd166): VehicleMeshBundle {
    const group = new THREE.Group();
    group.name = `Vehicle_Truck_${id}`;

    const cabMat = new THREE.MeshStandardMaterial({ color, roughness: 0.5, metalness: 0.5 });
    const boxMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.6 });
    this.disposables.push(cabMat, boxMat);

    // Driver Cab: 2.3m x 2.2m x 2.0m (Front)
    const cabGeo = new THREE.BoxGeometry(2.3, 2.1, 2.0);
    const cab = new THREE.Mesh(cabGeo, cabMat);
    cab.position.set(0, 1.5, 2.2);
    group.add(cab);

    // Cab Windshield
    const shieldGeo = new THREE.BoxGeometry(2.1, 0.8, 0.1);
    const shield = new THREE.Mesh(shieldGeo, this.glassMat);
    shield.position.set(0, 1.85, 3.21);
    group.add(shield);

    // Cargo Container Box: 2.4m x 2.6m x 5.2m (Rear)
    const boxGeo = new THREE.BoxGeometry(2.4, 2.5, 5.2);
    const cargoBox = new THREE.Mesh(boxGeo, boxMat);
    cargoBox.position.set(0, 1.8, -1.3);
    group.add(cargoBox);

    // Wheels
    this.addVehicleWheels(group, 1.15, 0.45, 2.2);

    // Rear Dual Axle Wheels
    const wheelGeo = new THREE.CylinderGeometry(0.45, 0.45, 0.28, 14);
    wheelGeo.rotateZ(Math.PI / 2);
    const rw1 = new THREE.Mesh(wheelGeo, this.tireMat);
    rw1.position.set(1.15, 0.45, -2.4);
    const rw2 = new THREE.Mesh(wheelGeo, this.tireMat);
    rw2.position.set(-1.15, 0.45, -2.4);
    group.add(rw1, rw2);

    this.addFrontHeadlights(group, 0.85, 0.75, 3.22);
    this.addRearTaillights(group, 0.95, 0.85, -3.92);

    this.disposables.push(cabGeo, shieldGeo, boxGeo, wheelGeo);

    return { group, vehicleClass: 'truck', id };
  }

  /**
   * 6. Emergency Ambulance (AMB-339 Priority Vehicle)
   */
  public createEmergencyAmbulance(id: string = 'AMB-339'): VehicleMeshBundle {
    const group = new THREE.Group();
    group.name = `Vehicle_Ambulance_${id}`;

    const whiteBodyMat = new THREE.MeshStandardMaterial({
      color: 0xf8fafc,
      roughness: 0.3,
      metalness: 0.2,
    });
    const redDecalMat = new THREE.MeshBasicMaterial({ color: 0xef476f });
    const chevronMat = new THREE.MeshBasicMaterial({ color: 0xffd166 });
    this.disposables.push(whiteBodyMat, redDecalMat, chevronMat);

    // Main Ambulance Box Body: 2.2m x 2.2m x 5.2m
    const bodyGeo = new THREE.BoxGeometry(2.2, 2.1, 5.2);
    const body = new THREE.Mesh(bodyGeo, whiteBodyMat);
    body.position.set(0, 1.45, 0);
    body.castShadow = true;
    group.add(body);

    // Driver Cab Sloped Front
    const cabGeo = new THREE.BoxGeometry(2.1, 1.4, 1.5);
    const cab = new THREE.Mesh(cabGeo, whiteBodyMat);
    cab.position.set(0, 1.1, 2.2);
    group.add(cab);

    // Windshield
    const windshieldGeo = new THREE.BoxGeometry(1.9, 0.65, 0.1);
    const windshield = new THREE.Mesh(windshieldGeo, this.glassMat);
    windshield.position.set(0, 1.35, 2.96);
    group.add(windshield);

    // Medical Red Cross Decals on Sides
    const crossBar1Geo = new THREE.PlaneGeometry(0.3, 1.1);
    const crossBar2Geo = new THREE.PlaneGeometry(1.1, 0.3);

    // Left Flank Cross
    const c1L = new THREE.Mesh(crossBar1Geo, redDecalMat);
    c1L.position.set(-1.11, 1.6, 0);
    c1L.rotation.y = -Math.PI / 2;
    const c2L = new THREE.Mesh(crossBar2Geo, redDecalMat);
    c2L.position.set(-1.11, 1.6, 0);
    c2L.rotation.y = -Math.PI / 2;
    group.add(c1L, c2L);

    // Right Flank Cross
    const c1R = new THREE.Mesh(crossBar1Geo, redDecalMat);
    c1R.position.set(1.11, 1.6, 0);
    c1R.rotation.y = Math.PI / 2;
    const c2R = new THREE.Mesh(crossBar2Geo, redDecalMat);
    c2R.position.set(1.11, 1.6, 0);
    c2R.rotation.y = Math.PI / 2;
    group.add(c1R, c2R);

    // Rear Chevrons (Yellow/Red reflective hazard pattern)
    const chevronGeo = new THREE.PlaneGeometry(1.8, 0.4);
    const chevron = new THREE.Mesh(chevronGeo, chevronMat);
    chevron.position.set(0, 0.7, -2.61);
    chevron.rotation.y = Math.PI;
    group.add(chevron);

    // Rooftop Strobe Lightbar (Dual Alternating Red & Cyan Strobes)
    const lightbarBaseGeo = new THREE.BoxGeometry(1.6, 0.15, 0.35);
    const lightbarBase = new THREE.Mesh(lightbarBaseGeo, new THREE.MeshStandardMaterial({ color: 0x1e293b }));
    lightbarBase.position.set(0, 2.58, 0.6);
    group.add(lightbarBase);

    const strobeLeftMat = new THREE.MeshBasicMaterial({ color: 0xef476f });
    const strobeRightMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff });
    this.disposables.push(strobeLeftMat, strobeRightMat);

    const strobeGeo = new THREE.BoxGeometry(0.65, 0.18, 0.28);

    const strobeLeft = new THREE.Mesh(strobeGeo, strobeLeftMat);
    strobeLeft.position.set(-0.45, 2.7, 0.6);
    group.add(strobeLeft);

    const strobeRight = new THREE.Mesh(strobeGeo, strobeRightMat);
    strobeRight.position.set(0.45, 2.7, 0.6);
    group.add(strobeRight);

    // Grille Strobe Warning Lights
    const grilleLeft = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.12, 0.05), strobeLeftMat);
    grilleLeft.position.set(-0.45, 0.8, 2.96);
    const grilleRight = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.12, 0.05), strobeRightMat);
    grilleRight.position.set(0.45, 0.8, 2.96);
    group.add(grilleLeft, grilleRight);

    // Wheels
    this.addVehicleWheels(group, 1.1, 0.38, 1.6);

    // Headlights & Taillights
    this.addFrontHeadlights(group, 0.8, 0.8, 2.96);
    this.addRearTaillights(group, 0.85, 0.8, -2.61);

    this.disposables.push(
      bodyGeo,
      cabGeo,
      windshieldGeo,
      crossBar1Geo,
      crossBar2Geo,
      chevronGeo,
      lightbarBaseGeo,
      strobeGeo
    );

    // Strobe Animation Function: Alternating Red/Cyan high-intensity strobe pulses
    const update = (timeMs: number) => {
      const isRedPhase = Math.floor(timeMs * 0.008) % 2 === 0;
      strobeLeftMat.color.setHex(isRedPhase ? 0xff0044 : 0x220005);
      strobeRightMat.color.setHex(!isRedPhase ? 0x00e5ff : 0x001a22);
    };

    return {
      group,
      vehicleClass: 'emergency_ambulance',
      id,
      strobeMaterials: [strobeLeftMat, strobeRightMat],
      update,
    };
  }

  /**
   * 7. Emergency Fire Engine (Xe cứu hỏa)
   */
  public createEmergencyFireEngine(id: string = 'FIRE-09'): VehicleMeshBundle {
    const group = new THREE.Group();
    group.name = `Vehicle_FireEngine_${id}`;

    const redMat = new THREE.MeshStandardMaterial({ color: 0xdc2626, roughness: 0.3, metalness: 0.4 });
    const silverMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8 });
    this.disposables.push(redMat, silverMat);

    // Rescue Body: 2.5m x 3.0m x 8.4m
    const bodyGeo = new THREE.BoxGeometry(2.5, 2.8, 8.4);
    const body = new THREE.Mesh(bodyGeo, redMat);
    body.position.set(0, 1.8, 0);
    group.add(body);

    // Crew Cab Front
    const cabGeo = new THREE.BoxGeometry(2.4, 2.4, 2.4);
    const cab = new THREE.Mesh(cabGeo, redMat);
    cab.position.set(0, 1.6, 3.2);
    group.add(cab);

    // Rooftop Rescue Ladder (2 silver side rails + rungs)
    const ladderGeo = new THREE.BoxGeometry(0.8, 0.15, 6.5);
    const ladder = new THREE.Mesh(ladderGeo, silverMat);
    ladder.position.set(0, 3.3, -0.6);
    group.add(ladder);

    // 4 Revolving Siren Beacons on Roof
    const beaconMat = new THREE.MeshBasicMaterial({ color: 0xef476f });
    this.disposables.push(beaconMat);

    const beaconGeo = new THREE.CylinderGeometry(0.18, 0.18, 0.25, 8);
    const b1 = new THREE.Mesh(beaconGeo, beaconMat);
    b1.position.set(-0.9, 2.9, 3.2);
    const b2 = new THREE.Mesh(beaconGeo, beaconMat);
    b2.position.set(0.9, 2.9, 3.2);
    group.add(b1, b2);

    // Wheels (6 heavy wheels)
    this.addVehicleWheels(group, 1.25, 0.5, 2.8);

    const rwGeo = new THREE.CylinderGeometry(0.5, 0.5, 0.32, 14);
    rwGeo.rotateZ(Math.PI / 2);
    const rw1 = new THREE.Mesh(rwGeo, this.tireMat);
    rw1.position.set(1.25, 0.5, -2.6);
    const rw2 = new THREE.Mesh(rwGeo, this.tireMat);
    rw2.position.set(-1.25, 0.5, -2.6);
    group.add(rw1, rw2);

    this.addFrontHeadlights(group, 0.95, 0.9, 4.41);
    this.addRearTaillights(group, 0.95, 0.95, -4.21);

    this.disposables.push(bodyGeo, cabGeo, ladderGeo, beaconGeo, rwGeo);

    const update = (timeMs: number) => {
      const pulse = (Math.sin(timeMs * 0.012) + 1) / 2;
      beaconMat.color.setRGB(0.9 + 0.1 * pulse, 0.1 * pulse, 0.1 * pulse);
    };

    return { group, vehicleClass: 'emergency_fire', id, update };
  }

  // --- Helper Methods ---

  private addVehicleWheels(group: THREE.Group, trackWidth: number, radius: number, wheelbase: number): void {
    const wheelGeo = new THREE.CylinderGeometry(radius, radius, 0.25, 14);
    wheelGeo.rotateZ(Math.PI / 2);

    const positions = [
      { x: trackWidth, z: wheelbase },
      { x: -trackWidth, z: wheelbase },
      { x: trackWidth, z: -wheelbase },
      { x: -trackWidth, z: -wheelbase },
    ];

    positions.forEach((p) => {
      const wheel = new THREE.Mesh(wheelGeo, this.tireMat);
      wheel.position.set(p.x, radius, p.z);
      group.add(wheel);
    });

    this.disposables.push(wheelGeo);
  }

  private addFrontHeadlights(group: THREE.Group, xOffset: number, y: number, z: number): void {
    const lightGeo = new THREE.SphereGeometry(0.12, 8, 8);
    const l1 = new THREE.Mesh(lightGeo, this.headlightMat);
    l1.position.set(-xOffset, y, z);
    const l2 = new THREE.Mesh(lightGeo, this.headlightMat);
    l2.position.set(xOffset, y, z);
    group.add(l1, l2);
    this.disposables.push(lightGeo);
  }

  private addRearTaillights(group: THREE.Group, xOffset: number, y: number, z: number): void {
    const lightGeo = new THREE.BoxGeometry(0.25, 0.1, 0.05);
    const l1 = new THREE.Mesh(lightGeo, this.taillightMat);
    l1.position.set(-xOffset, y, z);
    const l2 = new THREE.Mesh(lightGeo, this.taillightMat);
    l2.position.set(xOffset, y, z);
    group.add(l1, l2);
    this.disposables.push(lightGeo);
  }

  public dispose(): void {
    this.disposables.forEach((d) => {
      try {
        d.dispose();
      } catch (e) {
        // Ignore
      }
    });
  }
}

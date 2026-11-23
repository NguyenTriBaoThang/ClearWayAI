/**
 * ClearWayAI Multi-Intersection 3D Road Network (`apps/web/src/features/digital-twin/MultiIntersectionRoadNetwork.ts`)
 *
 * Procedurally generates the complete 1,000m arterial corridor (5th Avenue) with 4 sequential
 * orthogonal intersections:
 * - Node A: Maple St (x = 0m, z = 0m)
 * - Node B: Oak St / INT-0457 (x = 250m, z = 0m)
 * - Node C: Pine St (x = 500m, z = 0m)
 * - Node D: Elm St (x = 750m, z = 0m)
 * - Trauma Center Approach: x = 850m
 *
 * Includes asphalt roadway (4 lanes, 14m width), 4 cross streets, double yellow centerlines,
 * dashed white lane dividers, solid stop lines, zebra pedestrian crosswalks, and conflict boxes.
 */

import * as THREE from 'three';

export interface CorridorNodeTopology {
  id: string;
  name: string;
  crossStreet: string;
  xMeters: number;
  zMeters: number;
}

export const ARTERIAL_NODES: CorridorNodeTopology[] = [
  { id: 'node_a', name: 'Node A', crossStreet: 'Maple St', xMeters: 0, zMeters: 0 },
  { id: 'node_b', name: 'Node B', crossStreet: 'Oak St (INT-0457)', xMeters: 250, zMeters: 0 },
  { id: 'node_c', name: 'Node C', crossStreet: 'Pine St', xMeters: 500, zMeters: 0 },
  { id: 'node_d', name: 'Node D', crossStreet: 'Elm St', xMeters: 750, zMeters: 0 },
];

export class MultiIntersectionRoadNetwork {
  public group: THREE.Group;
  public readonly nodes: CorridorNodeTopology[] = ARTERIAL_NODES;

  // Subgroups for selective visibility toggling
  public asphaltGroup: THREE.Group;
  public sidewalksGroup: THREE.Group;
  public markingsGroup: THREE.Group;
  public crosswalksGroup: THREE.Group;
  public conflictBoxesGroup: THREE.Group;

  private disposables: { dispose: () => void }[] = [];

  constructor() {
    this.group = new THREE.Group();
    this.group.name = 'MultiIntersectionRoadNetwork';

    this.asphaltGroup = new THREE.Group();
    this.asphaltGroup.name = 'ArterialAsphalt';
    this.sidewalksGroup = new THREE.Group();
    this.sidewalksGroup.name = 'ArterialSidewalks';
    this.markingsGroup = new THREE.Group();
    this.markingsGroup.name = 'ArterialMarkings';
    this.crosswalksGroup = new THREE.Group();
    this.crosswalksGroup.name = 'ArterialCrosswalks';
    this.conflictBoxesGroup = new THREE.Group();
    this.conflictBoxesGroup.name = 'ConflictBoxes';

    this.group.add(this.asphaltGroup);
    this.group.add(this.sidewalksGroup);
    this.group.add(this.markingsGroup);
    this.group.add(this.crosswalksGroup);
    this.group.add(this.conflictBoxesGroup);

    this.buildArterialCorridorRoadway();
    this.buildCrossStreets();
    this.buildCenterDividers();
    this.buildLaneMarkings();
    this.buildStopLinesAndCrosswalks();
    this.buildConflictBoxes();
  }

  /**
   * 1. Continuous Arterial 5th Avenue Roadway (x: -150m to 900m = 1,050m span)
   */
  private buildArterialCorridorRoadway(): void {
    const roadWidth = 14.0; // 4 lanes * 3.5m
    const totalLength = 1050.0;
    const centerX = 375.0; // (-150 + 900) / 2 = 375m

    const roadMat = new THREE.MeshStandardMaterial({
      color: 0x141d36,
      roughness: 0.88,
      metalness: 0.12,
    });
    this.disposables.push(roadMat);

    const geo = new THREE.PlaneGeometry(totalLength, roadWidth);
    const mesh = new THREE.Mesh(geo, roadMat);
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.set(centerX, 0.01, 0);
    mesh.receiveShadow = true;
    this.asphaltGroup.add(mesh);

    // Arterial Sidewalks (North and South sides)
    const curbMat = new THREE.MeshStandardMaterial({
      color: 0x1e2c4f,
      roughness: 0.65,
    });
    const neonCurbMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff });
    this.disposables.push(curbMat, neonCurbMat);

    // North sidewalk
    const northSidewalkGeo = new THREE.BoxGeometry(totalLength, 0.3, 4.0);
    const northSidewalk = new THREE.Mesh(northSidewalkGeo, curbMat);
    northSidewalk.position.set(centerX, 0.15, -9.0);
    this.sidewalksGroup.add(northSidewalk);

    // South sidewalk
    const southSidewalk = new THREE.Mesh(northSidewalkGeo, curbMat);
    southSidewalk.position.set(centerX, 0.15, 9.0);
    this.sidewalksGroup.add(southSidewalk);

    // Neon curb edge lines
    const curbLineGeo = new THREE.BoxGeometry(totalLength, 0.05, 0.1);
    const northCurbEdge = new THREE.Mesh(curbLineGeo, neonCurbMat);
    northCurbEdge.position.set(centerX, 0.31, -7.05);
    this.sidewalksGroup.add(northCurbEdge);

    const southCurbEdge = new THREE.Mesh(curbLineGeo, neonCurbMat);
    southCurbEdge.position.set(centerX, 0.31, 7.05);
    this.sidewalksGroup.add(southCurbEdge);
  }

  /**
   * 2. Orthogonal Cross Streets at Nodes A, B, C, D
   */
  private buildCrossStreets(): void {
    const crossStreetWidth = 14.0;
    const crossStreetLength = 80.0; // 40m North, 40m South

    const crossMat = new THREE.MeshStandardMaterial({
      color: 0x121a30,
      roughness: 0.88,
      metalness: 0.12,
    });
    this.disposables.push(crossMat);

    for (const node of this.nodes) {
      // Cross street asphalt
      const crossGeo = new THREE.PlaneGeometry(crossStreetWidth, crossStreetLength);
      const crossMesh = new THREE.Mesh(crossGeo, crossMat);
      crossMesh.rotation.x = -Math.PI / 2;
      crossMesh.position.set(node.xMeters, 0.015, 0);
      crossMesh.receiveShadow = true;
      this.asphaltGroup.add(crossMesh);
    }
  }

  /**
   * 3. Double Yellow Centerlines along 5th Avenue
   */
  private buildCenterDividers(): void {
    const yellowMat = new THREE.MeshBasicMaterial({ color: 0xffd166 });
    this.disposables.push(yellowMat);

    // Between each node segment (skip intersection conflict zones)
    const segments = [
      { startX: -150, endX: -10 },
      { startX: 10, endX: 240 },
      { startX: 260, endX: 490 },
      { startX: 510, endX: 740 },
      { startX: 760, endX: 890 },
    ];

    for (const seg of segments) {
      const len = seg.endX - seg.startX;
      const midX = (seg.startX + seg.endX) / 2;

      // Double yellow line 1
      const line1Geo = new THREE.PlaneGeometry(len, 0.15);
      const line1 = new THREE.Mesh(line1Geo, yellowMat);
      line1.rotation.x = -Math.PI / 2;
      line1.position.set(midX, 0.02, -0.12);
      this.markingsGroup.add(line1);

      // Double yellow line 2
      const line2 = new THREE.Mesh(line1Geo, yellowMat);
      line2.rotation.x = -Math.PI / 2;
      line2.position.set(midX, 0.02, 0.12);
      this.markingsGroup.add(line2);
    }
  }

  /**
   * 4. Dashed White Lane Dividers
   */
  private buildLaneMarkings(): void {
    const whiteMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    this.disposables.push(whiteMat);

    const segments = [
      { startX: -140, endX: -12 },
      { startX: 12, endX: 238 },
      { startX: 262, endX: 488 },
      { startX: 512, endX: 738 },
      { startX: 762, endX: 880 },
    ];

    for (const seg of segments) {
      for (let x = seg.startX; x < seg.endX; x += 6) {
        // North side lane divider (z = -3.5m)
        const dashGeo = new THREE.PlaneGeometry(3.0, 0.15);
        const dashN = new THREE.Mesh(dashGeo, whiteMat);
        dashN.rotation.x = -Math.PI / 2;
        dashN.position.set(x + 1.5, 0.02, -3.5);
        this.markingsGroup.add(dashN);

        // South side lane divider (z = +3.5m)
        const dashS = new THREE.Mesh(dashGeo, whiteMat);
        dashS.rotation.x = -Math.PI / 2;
        dashS.position.set(x + 1.5, 0.02, 3.5);
        this.markingsGroup.add(dashS);
      }
    }
  }

  /**
   * 5. Solid Stop Lines and Zebra Crosswalks at all 4 Intersections
   */
  private buildStopLinesAndCrosswalks(): void {
    const whiteMat = new THREE.MeshBasicMaterial({ color: 0xf8fafc });
    this.disposables.push(whiteMat);

    for (const node of this.nodes) {
      // West Stop Line (Eastbound approach to node)
      const stopLineGeo = new THREE.PlaneGeometry(0.5, 7.0);
      const stopLineW = new THREE.Mesh(stopLineGeo, whiteMat);
      stopLineW.rotation.x = -Math.PI / 2;
      stopLineW.position.set(node.xMeters - 10.5, 0.025, 3.5); // South side EB lane
      this.markingsGroup.add(stopLineW);

      // East Stop Line (Westbound approach to node)
      const stopLineE = new THREE.Mesh(stopLineGeo, whiteMat);
      stopLineE.rotation.x = -Math.PI / 2;
      stopLineE.position.set(node.xMeters + 10.5, 0.025, -3.5); // North side WB lane
      this.markingsGroup.add(stopLineE);

      // West Crosswalk Zebra Stripes
      for (let z = -6.0; z <= 6.0; z += 1.4) {
        const stripeGeo = new THREE.PlaneGeometry(3.0, 0.6);
        const stripe = new THREE.Mesh(stripeGeo, whiteMat);
        stripe.rotation.x = -Math.PI / 2;
        stripe.position.set(node.xMeters - 8.5, 0.022, z);
        this.crosswalksGroup.add(stripe);
      }

      // East Crosswalk Zebra Stripes
      for (let z = -6.0; z <= 6.0; z += 1.4) {
        const stripeGeo = new THREE.PlaneGeometry(3.0, 0.6);
        const stripe = new THREE.Mesh(stripeGeo, whiteMat);
        stripe.rotation.x = -Math.PI / 2;
        stripe.position.set(node.xMeters + 8.5, 0.022, z);
        this.crosswalksGroup.add(stripe);
      }
    }
  }

  /**
   * 6. Yellow Intersection Conflict Boxes
   */
  private buildConflictBoxes(): void {
    const yellowMat = new THREE.MeshBasicMaterial({
      color: 0xffd166,
      transparent: true,
      opacity: 0.25,
    });
    this.disposables.push(yellowMat);

    for (const node of this.nodes) {
      const boxGeo = new THREE.PlaneGeometry(14.0, 14.0);
      const box = new THREE.Mesh(boxGeo, yellowMat);
      box.rotation.x = -Math.PI / 2;
      box.position.set(node.xMeters, 0.02, 0);
      this.conflictBoxesGroup.add(box);
    }
  }

  public setMarkingsVisibility(visible: boolean): void {
    this.markingsGroup.visible = visible;
  }

  public setCrosswalksVisibility(visible: boolean): void {
    this.crosswalksGroup.visible = visible;
  }

  public setSidewalksVisibility(visible: boolean): void {
    this.sidewalksGroup.visible = visible;
  }

  public dispose(): void {
    for (const d of this.disposables) {
      d.dispose();
    }
  }
}

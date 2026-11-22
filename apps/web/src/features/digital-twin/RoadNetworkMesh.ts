import * as THREE from 'three';
import { INTERSECTION_CONFIG, RoadNetworkConfig } from './roadNetworkData';

/**
 * RoadNetworkMesh generates procedural 3D geometry for intersection roadways:
 * - Asphalt road surface (orthogonal cross)
 * - Elevated corner sidewalks with neon cyber curbs
 * - Double yellow center dividing lines
 * - Dashed white lane lines
 * - Solid stop lines
 * - High-contrast zebra pedestrian crosswalks
 * - Directional pavement lane arrows (Thru, Left, Right)
 * - Intersection conflict box markings
 */
export class RoadNetworkMesh {
  public group: THREE.Group;
  public config: RoadNetworkConfig;

  // Subgroups for selective layer visibility toggling
  private asphaltGroup: THREE.Group;
  private sidewalksGroup: THREE.Group;
  private markingsGroup: THREE.Group;
  private crosswalksGroup: THREE.Group;
  private arrowsGroup: THREE.Group;

  private disposables: { dispose: () => void }[] = [];

  constructor(config: RoadNetworkConfig = INTERSECTION_CONFIG) {
    this.config = config;
    this.group = new THREE.Group();
    this.group.name = 'RoadNetwork';

    this.asphaltGroup = new THREE.Group();
    this.asphaltGroup.name = 'Asphalt';
    this.sidewalksGroup = new THREE.Group();
    this.sidewalksGroup.name = 'Sidewalks';
    this.markingsGroup = new THREE.Group();
    this.markingsGroup.name = 'Markings';
    this.crosswalksGroup = new THREE.Group();
    this.crosswalksGroup.name = 'Crosswalks';
    this.arrowsGroup = new THREE.Group();
    this.arrowsGroup.name = 'DirectionalArrows';

    this.group.add(this.asphaltGroup);
    this.group.add(this.sidewalksGroup);
    this.group.add(this.markingsGroup);
    this.group.add(this.crosswalksGroup);
    this.group.add(this.arrowsGroup);

    this.buildAsphaltSurfaces();
    this.buildSidewalks();
    this.buildCenterDividers();
    this.buildLaneDividers();
    this.buildStopLines();
    this.buildCrosswalks();
    this.buildDirectionalArrows();
    this.buildConflictBox();
  }

  /**
   * 1. Asphalt Road Surfaces
   */
  private buildAsphaltSurfaces(): void {
    const roadWidth = this.config.totalRoadWidthMeters; // 14m
    const totalLength = this.config.armLengthMeters * 2; // 80m

    const roadMat = new THREE.MeshStandardMaterial({
      color: 0x141d36,
      roughness: 0.88,
      metalness: 0.12,
    });
    this.disposables.push(roadMat);

    // East-West Corridor (5th Ave)
    const ewGeo = new THREE.PlaneGeometry(totalLength, roadWidth);
    const ewMesh = new THREE.Mesh(ewGeo, roadMat);
    ewMesh.rotation.x = -Math.PI / 2;
    ewMesh.position.y = 0.01;
    ewMesh.receiveShadow = true;
    this.asphaltGroup.add(ewMesh);
    this.disposables.push(ewGeo);

    // North-South Corridor (Oak St)
    const nsGeo = new THREE.PlaneGeometry(roadWidth, totalLength);
    const nsMesh = new THREE.Mesh(nsGeo, roadMat);
    nsMesh.rotation.x = -Math.PI / 2;
    nsMesh.position.y = 0.011; // tiny offset to avoid z-fight at crossing
    nsMesh.receiveShadow = true;
    this.asphaltGroup.add(nsMesh);
    this.disposables.push(nsGeo);
  }

  /**
   * 2. Elevated Corner Sidewalks & Curbs
   */
  private buildSidewalks(): void {
    const roadHalfWidth = this.config.totalRoadWidthMeters / 2; // 7m
    const sidewalkSize = 32.0; // 32m x 32m corner blocks
    const sidewalkHeight = 0.22;
    const centerOffset = roadHalfWidth + sidewalkSize / 2; // 7 + 16 = 23m

    const sidewalkMat = new THREE.MeshStandardMaterial({
      color: 0x1b284a,
      roughness: 0.8,
      metalness: 0.2,
    });
    const curbEdgeMat = new THREE.LineBasicMaterial({ color: 0x00e5ff });
    this.disposables.push(sidewalkMat, curbEdgeMat);

    const corners = [
      { x: -centerOffset, z: -centerOffset, name: 'Sidewalk_NW' },
      { x: centerOffset, z: -centerOffset, name: 'Sidewalk_NE' },
      { x: -centerOffset, z: centerOffset, name: 'Sidewalk_SW' },
      { x: centerOffset, z: centerOffset, name: 'Sidewalk_SE' },
    ];

    corners.forEach((corner) => {
      const geo = new THREE.BoxGeometry(sidewalkSize, sidewalkHeight, sidewalkSize);
      const mesh = new THREE.Mesh(geo, sidewalkMat);
      mesh.position.set(corner.x, sidewalkHeight / 2, corner.z);
      mesh.receiveShadow = true;
      mesh.castShadow = true;
      this.sidewalksGroup.add(mesh);

      // Cyber glowing curb lines along sidewalk edges facing the streets
      const edges = new THREE.EdgesGeometry(geo);
      const edgeLines = new THREE.LineSegments(edges, curbEdgeMat);
      edgeLines.position.copy(mesh.position);
      this.sidewalksGroup.add(edgeLines);

      this.disposables.push(geo, edges);
    });
  }

  /**
   * 3. Double Yellow Center Dividing Lines
   */
  private buildCenterDividers(): void {
    const yellowMat = new THREE.MeshBasicMaterial({ color: 0xffd166 });
    this.disposables.push(yellowMat);

    const lineWidth = 0.14;
    const gap = 0.14;
    const startDist = 12.0;
    const endDist = this.config.armLengthMeters; // 40m
    const segmentLength = endDist - startDist; // 28m
    const midDist = (startDist + endDist) / 2; // 26m

    // North Approach Center Double Line
    this.createDoubleLinePair(0, -midDist, lineWidth, segmentLength, gap, 'VERTICAL', yellowMat);

    // South Approach Center Double Line
    this.createDoubleLinePair(0, midDist, lineWidth, segmentLength, gap, 'VERTICAL', yellowMat);

    // East Approach Center Double Line
    this.createDoubleLinePair(midDist, 0, segmentLength, lineWidth, gap, 'HORIZONTAL', yellowMat);

    // West Approach Center Double Line
    this.createDoubleLinePair(-midDist, 0, segmentLength, lineWidth, gap, 'HORIZONTAL', yellowMat);
  }

  private createDoubleLinePair(
    cx: number,
    cz: number,
    w: number,
    h: number,
    gap: number,
    orientation: 'VERTICAL' | 'HORIZONTAL',
    mat: THREE.Material
  ): void {
    const geo = new THREE.PlaneGeometry(w, h);
    this.disposables.push(geo);

    if (orientation === 'VERTICAL') {
      // Offset along X
      const m1 = new THREE.Mesh(geo, mat);
      m1.rotation.x = -Math.PI / 2;
      m1.position.set(cx - gap / 2 - w / 2, 0.02, cz);
      const m2 = new THREE.Mesh(geo, mat);
      m2.rotation.x = -Math.PI / 2;
      m2.position.set(cx + gap / 2 + w / 2, 0.02, cz);
      this.markingsGroup.add(m1, m2);
    } else {
      // Offset along Z
      const m1 = new THREE.Mesh(geo, mat);
      m1.rotation.x = -Math.PI / 2;
      m1.position.set(cx, 0.02, cz - gap / 2 - h / 2);
      const m2 = new THREE.Mesh(geo, mat);
      m2.rotation.x = -Math.PI / 2;
      m2.position.set(cx, 0.02, cz + gap / 2 + h / 2);
      this.markingsGroup.add(m1, m2);
    }
  }

  /**
   * 4. Dashed White Lane Dividers
   */
  private buildLaneDividers(): void {
    const whiteMat = new THREE.MeshBasicMaterial({ color: 0xe2e8f0 });
    this.disposables.push(whiteMat);

    const laneWidth = this.config.laneWidthMeters; // 3.5m
    const dashLength = 2.4;
    const dashGap = 2.4;
    const lineWidth = 0.14;

    const startDist = 12.5;
    const endDist = 38.0;

    // Subdivide into dashes along each road approach at +/- laneWidth
    for (let d = startDist; d + dashLength <= endDist; d += dashLength + dashGap) {
      const centerDist = d + dashLength / 2;

      // North Arm (+3.5m and -3.5m)
      this.addDashedStripe(laneWidth, -centerDist, lineWidth, dashLength, whiteMat);
      this.addDashedStripe(-laneWidth, -centerDist, lineWidth, dashLength, whiteMat);

      // South Arm (+3.5m and -3.5m)
      this.addDashedStripe(laneWidth, centerDist, lineWidth, dashLength, whiteMat);
      this.addDashedStripe(-laneWidth, centerDist, lineWidth, dashLength, whiteMat);

      // East Arm
      this.addDashedStripe(centerDist, laneWidth, dashLength, lineWidth, whiteMat);
      this.addDashedStripe(centerDist, -laneWidth, dashLength, lineWidth, whiteMat);

      // West Arm
      this.addDashedStripe(-centerDist, laneWidth, dashLength, lineWidth, whiteMat);
      this.addDashedStripe(-centerDist, -laneWidth, dashLength, lineWidth, whiteMat);
    }
  }

  private addDashedStripe(x: number, z: number, w: number, h: number, mat: THREE.Material): void {
    const geo = new THREE.PlaneGeometry(w, h);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.set(x, 0.022, z);
    this.markingsGroup.add(mesh);
    this.disposables.push(geo);
  }

  /**
   * 5. Solid White Stop Lines
   */
  private buildStopLines(): void {
    const stopLineMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    this.disposables.push(stopLineMat);

    const stopLineThickness = 0.55;
    const halfRoadWidth = this.config.totalRoadWidthMeters / 2; // 7.0m
    const incomingWidth = halfRoadWidth; // 7.0m across 2 incoming lanes
    const stopDist = 11.5; // 11.5m from intersection center

    // North approach incoming: right half (x: 0 to 7), z = -stopDist
    this.createRectStripe(incomingWidth / 2, -stopDist, incomingWidth, stopLineThickness, stopLineMat);

    // South approach incoming: left half (x: -7 to 0), z = stopDist
    this.createRectStripe(-incomingWidth / 2, stopDist, incomingWidth, stopLineThickness, stopLineMat);

    // East approach incoming: bottom half (z: 0 to 7), x = stopDist
    this.createRectStripe(stopDist, incomingWidth / 2, stopLineThickness, incomingWidth, stopLineMat);

    // West approach incoming: top half (z: -7 to 0), x = -stopDist
    this.createRectStripe(-stopDist, -incomingWidth / 2, stopLineThickness, incomingWidth, stopLineMat);
  }

  /**
   * 6. Zebra Pedestrian Crosswalks (Across all 4 approaches)
   */
  private buildCrosswalks(): void {
    const crosswalkMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    this.disposables.push(crosswalkMat);

    const stripeWidth = 0.6; // Width of each white stripe
    const stripeLength = 3.2; // Length across the walking direction
    const stripeSpacing = 0.55; // Spacing between stripes
    const distFromCenter = 8.8; // Located 8.8m from junction center
    const roadWidth = this.config.totalRoadWidthMeters; // 14m
    const numStripes = 10;
    const spanStart = -(numStripes - 1) * (stripeWidth + stripeSpacing) / 2;

    for (let i = 0; i < numStripes; i++) {
      const offset = spanStart + i * (stripeWidth + stripeSpacing);

      // North Crosswalk: stripes along X, positioned at z = -distFromCenter
      this.createRectStripe(offset, -distFromCenter, stripeWidth, stripeLength, crosswalkMat);

      // South Crosswalk: stripes along X, positioned at z = distFromCenter
      this.createRectStripe(offset, distFromCenter, stripeWidth, stripeLength, crosswalkMat);

      // East Crosswalk: stripes along Z, positioned at x = distFromCenter
      this.createRectStripe(distFromCenter, offset, stripeLength, stripeWidth, crosswalkMat);

      // West Crosswalk: stripes along Z, positioned at x = -distFromCenter
      this.createRectStripe(-distFromCenter, offset, stripeLength, stripeWidth, crosswalkMat);
    }
  }

  /**
   * 7. Directional Lane Arrows (Thru, Left, Right)
   */
  private buildDirectionalArrows(): void {
    const arrowMat = new THREE.MeshBasicMaterial({ color: 0xf1f5f9 });
    this.disposables.push(arrowMat);

    const arrowDist = 16.5; // ~5m behind the stop line
    const lane1Offset = 1.75; // Center of inner lane (Left/Thru)
    const lane2Offset = 5.25; // Center of outer lane (Right/Thru)

    // North Approach Incoming (Facing South towards junction)
    this.createThruArrow(lane1Offset, -arrowDist, 'SOUTH', arrowMat);
    this.createRightTurnArrow(lane2Offset, -arrowDist, 'SOUTH', arrowMat);

    // South Approach Incoming (Facing North towards junction)
    this.createThruArrow(-lane1Offset, arrowDist, 'NORTH', arrowMat);
    this.createRightTurnArrow(-lane2Offset, arrowDist, 'NORTH', arrowMat);

    // East Approach Incoming (Facing West towards junction)
    this.createThruArrow(arrowDist, lane1Offset, 'WEST', arrowMat);
    this.createRightTurnArrow(arrowDist, lane2Offset, 'WEST', arrowMat);

    // West Approach Incoming (Facing East towards junction)
    this.createThruArrow(-arrowDist, -lane1Offset, 'EAST', arrowMat);
    this.createRightTurnArrow(-arrowDist, -lane2Offset, 'EAST', arrowMat);
  }

  private createThruArrow(
    x: number,
    z: number,
    direction: 'NORTH' | 'SOUTH' | 'EAST' | 'WEST',
    mat: THREE.Material
  ): void {
    const arrowGroup = new THREE.Group();

    // Stem: 0.35m x 2.2m
    const stemGeo = new THREE.PlaneGeometry(0.35, 2.2);
    const stem = new THREE.Mesh(stemGeo, mat);
    stem.rotation.x = -Math.PI / 2;
    stem.position.set(0, 0, -0.2);
    arrowGroup.add(stem);

    // Arrowhead: Triangular tip
    const headShape = new THREE.Shape();
    headShape.moveTo(0, 1.2);
    headShape.lineTo(0.65, 0.0);
    headShape.lineTo(-0.65, 0.0);
    headShape.closePath();
    const headGeo = new THREE.ShapeGeometry(headShape);
    const head = new THREE.Mesh(headGeo, mat);
    head.rotation.x = -Math.PI / 2;
    head.position.set(0, 0, 0.9);
    arrowGroup.add(head);

    this.disposables.push(stemGeo, headGeo);

    // Rotate according to road direction
    arrowGroup.position.set(x, 0.028, z);
    if (direction === 'SOUTH') arrowGroup.rotation.y = Math.PI;
    if (direction === 'EAST') arrowGroup.rotation.y = -Math.PI / 2;
    if (direction === 'WEST') arrowGroup.rotation.y = Math.PI / 2;

    this.arrowsGroup.add(arrowGroup);
  }

  private createRightTurnArrow(
    x: number,
    z: number,
    direction: 'NORTH' | 'SOUTH' | 'EAST' | 'WEST',
    mat: THREE.Material
  ): void {
    const arrowGroup = new THREE.Group();

    // Stem: 0.35m x 2.0m
    const stemGeo = new THREE.PlaneGeometry(0.35, 2.0);
    const stem = new THREE.Mesh(stemGeo, mat);
    stem.rotation.x = -Math.PI / 2;
    arrowGroup.add(stem);

    // Hook arm pointing to the right
    const hookGeo = new THREE.PlaneGeometry(1.0, 0.35);
    const hook = new THREE.Mesh(hookGeo, mat);
    hook.rotation.x = -Math.PI / 2;
    hook.position.set(0.45, 0, 0.85);
    arrowGroup.add(hook);

    // Arrowhead on the hook
    const headShape = new THREE.Shape();
    headShape.moveTo(1.4, 0.85);
    headShape.lineTo(0.85, 1.35);
    headShape.lineTo(0.85, 0.35);
    headShape.closePath();
    const headGeo = new THREE.ShapeGeometry(headShape);
    const head = new THREE.Mesh(headGeo, mat);
    head.rotation.x = -Math.PI / 2;
    arrowGroup.add(head);

    this.disposables.push(stemGeo, hookGeo, headGeo);

    arrowGroup.position.set(x, 0.028, z);
    if (direction === 'SOUTH') arrowGroup.rotation.y = Math.PI;
    if (direction === 'EAST') arrowGroup.rotation.y = -Math.PI / 2;
    if (direction === 'WEST') arrowGroup.rotation.y = Math.PI / 2;

    this.arrowsGroup.add(arrowGroup);
  }

  /**
   * 8. Intersection Conflict Zone Box Marking
   */
  private buildConflictBox(): void {
    const boxMat = new THREE.LineDashedMaterial({
      color: 0xffd166,
      dashSize: 1.0,
      gapSize: 0.8,
      linewidth: 1,
    });
    this.disposables.push(boxMat);

    const halfWidth = this.config.totalRoadWidthMeters / 2; // 7.0m
    const points = [
      new THREE.Vector3(-halfWidth, 0.025, -halfWidth),
      new THREE.Vector3(halfWidth, 0.025, -halfWidth),
      new THREE.Vector3(halfWidth, 0.025, halfWidth),
      new THREE.Vector3(-halfWidth, 0.025, halfWidth),
      new THREE.Vector3(-halfWidth, 0.025, -halfWidth),
    ];
    const geo = new THREE.BufferGeometry().setFromPoints(points);
    const boxLine = new THREE.Line(geo, boxMat);
    boxLine.computeLineDistances();
    this.markingsGroup.add(boxLine);
    this.disposables.push(geo);
  }

  private createRectStripe(
    cx: number,
    cz: number,
    width: number,
    height: number,
    mat: THREE.Material
  ): THREE.Mesh {
    const geo = new THREE.PlaneGeometry(width, height);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.set(cx, 0.025, cz);
    this.crosswalksGroup.add(mesh);
    this.disposables.push(geo);
    return mesh;
  }

  /**
   * Layer Visibility Controls
   */
  public setMarkingsVisibility(visible: boolean): void {
    this.markingsGroup.visible = visible;
    this.arrowsGroup.visible = visible;
  }

  public setCrosswalksVisibility(visible: boolean): void {
    this.crosswalksGroup.visible = visible;
  }

  public setSidewalksVisibility(visible: boolean): void {
    this.sidewalksGroup.visible = visible;
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

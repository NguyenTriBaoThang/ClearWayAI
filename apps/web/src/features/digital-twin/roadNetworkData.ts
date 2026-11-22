/**
 * Road Network Topology & Intersection Configuration for Oak St. & 5th Ave (INT-0457).
 * Adheres strictly to standard 3.5m lane widths, orthogonal 4-way geometry, and SI meters.
 */

export interface LaneDefinition {
  id: string;
  index: number; // 0 = inner/leftmost, 1 = outer/rightmost
  direction: 'INCOMING' | 'OUTGOING';
  widthMeters: number;
  allowedMovements: ('THRU' | 'LEFT' | 'RIGHT')[];
}

export interface ApproachDefinition {
  id: string;
  name: string;
  compassHeading: 'NORTH' | 'SOUTH' | 'EAST' | 'WEST';
  streetName: string;
  lengthMeters: number;
  totalWidthMeters: number;
  lanes: LaneDefinition[];
  crosswalkDistance: number;
  stopLineDistance: number;
}

export interface RoadNetworkConfig {
  intersectionId: string;
  intersectionName: string;
  laneWidthMeters: number;
  totalRoadWidthMeters: number;
  armLengthMeters: number;
  approaches: Record<'NORTH' | 'SOUTH' | 'EAST' | 'WEST', ApproachDefinition>;
}

export const INTERSECTION_CONFIG: RoadNetworkConfig = {
  intersectionId: 'INT-0457',
  intersectionName: 'Oak St. & 5th Ave',
  laneWidthMeters: 3.5,
  totalRoadWidthMeters: 14.0, // 4 lanes * 3.5m = 14m
  armLengthMeters: 40.0,
  approaches: {
    NORTH: {
      id: 'APP_NORTH',
      name: 'Oak St. (Northbound Approach)',
      compassHeading: 'NORTH',
      streetName: 'Oak St.',
      lengthMeters: 40.0,
      totalWidthMeters: 14.0,
      crosswalkDistance: 9.0,
      stopLineDistance: 11.5,
      lanes: [
        { id: 'OAK_NB_L1', index: 0, direction: 'INCOMING', widthMeters: 3.5, allowedMovements: ['THRU', 'LEFT'] },
        { id: 'OAK_NB_L2', index: 1, direction: 'INCOMING', widthMeters: 3.5, allowedMovements: ['THRU', 'RIGHT'] },
        { id: 'OAK_SB_L1', index: 0, direction: 'OUTGOING', widthMeters: 3.5, allowedMovements: ['THRU'] },
        { id: 'OAK_SB_L2', index: 1, direction: 'OUTGOING', widthMeters: 3.5, allowedMovements: ['THRU'] },
      ],
    },
    SOUTH: {
      id: 'APP_SOUTH',
      name: 'Oak St. (Southbound Approach)',
      compassHeading: 'SOUTH',
      streetName: 'Oak St.',
      lengthMeters: 40.0,
      totalWidthMeters: 14.0,
      crosswalkDistance: 9.0,
      stopLineDistance: 11.5,
      lanes: [
        { id: 'OAK_SB_L1_IN', index: 0, direction: 'INCOMING', widthMeters: 3.5, allowedMovements: ['THRU', 'LEFT'] },
        { id: 'OAK_SB_L2_IN', index: 1, direction: 'INCOMING', widthMeters: 3.5, allowedMovements: ['THRU', 'RIGHT'] },
        { id: 'OAK_NB_L1_OUT', index: 0, direction: 'OUTGOING', widthMeters: 3.5, allowedMovements: ['THRU'] },
        { id: 'OAK_NB_L2_OUT', index: 1, direction: 'OUTGOING', widthMeters: 3.5, allowedMovements: ['THRU'] },
      ],
    },
    EAST: {
      id: 'APP_EAST',
      name: '5th Ave. (Eastbound Approach)',
      compassHeading: 'EAST',
      streetName: '5th Ave.',
      lengthMeters: 40.0,
      totalWidthMeters: 14.0,
      crosswalkDistance: 9.0,
      stopLineDistance: 11.5,
      lanes: [
        { id: '5TH_EB_L1', index: 0, direction: 'INCOMING', widthMeters: 3.5, allowedMovements: ['THRU', 'LEFT'] },
        { id: '5TH_EB_L2', index: 1, direction: 'INCOMING', widthMeters: 3.5, allowedMovements: ['THRU', 'RIGHT'] },
        { id: '5TH_WB_L1', index: 0, direction: 'OUTGOING', widthMeters: 3.5, allowedMovements: ['THRU'] },
        { id: '5TH_WB_L2', index: 1, direction: 'OUTGOING', widthMeters: 3.5, allowedMovements: ['THRU'] },
      ],
    },
    WEST: {
      id: 'APP_WEST',
      name: '5th Ave. (Westbound Approach)',
      compassHeading: 'WEST',
      streetName: '5th Ave.',
      lengthMeters: 40.0,
      totalWidthMeters: 14.0,
      crosswalkDistance: 9.0,
      stopLineDistance: 11.5,
      lanes: [
        { id: '5TH_WB_L1_IN', index: 0, direction: 'INCOMING', widthMeters: 3.5, allowedMovements: ['THRU', 'LEFT'] },
        { id: '5TH_WB_L2_IN', index: 1, direction: 'INCOMING', widthMeters: 3.5, allowedMovements: ['THRU', 'RIGHT'] },
        { id: '5TH_EB_L1_OUT', index: 0, direction: 'OUTGOING', widthMeters: 3.5, allowedMovements: ['THRU'] },
        { id: '5TH_EB_L2_OUT', index: 1, direction: 'OUTGOING', widthMeters: 3.5, allowedMovements: ['THRU'] },
      ],
    },
  },
};

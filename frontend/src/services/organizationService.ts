import { ApiService } from './apiClient';

/**
 * 組織図サービス
 * P-003: 組織図ビューア機能のAPIサービス
 */

// 組織ノードインターフェース
export interface OrganizationNode {
  id: string;
  member_number: string;
  name: string;
  title: string;
  level: number;
  hierarchy_path: string;
  registration_date?: string;
  is_direct: boolean;
  is_withdrawn: boolean;
  
  // 組織実績
  left_count: number;
  right_count: number;
  left_sales: number;
  right_sales: number;
  new_purchase: number;
  repeat_purchase: number;
  additional_purchase: number;
  
  // フロントエンド用
  children: OrganizationNode[];
  is_expanded: boolean;
  status: string;
}

// 組織ツリーレスポンス
export interface OrganizationTree {
  root_nodes: OrganizationNode[];
  total_members: number;
  max_level: number;
  total_sales: number;
  active_members: number;
  withdrawn_members: number;
}

// 組織統計
export interface OrganizationStats {
  total_members: number;
  active_members: number;
  withdrawn_members: number;
  max_level: number;
  average_level: number;
  total_left_sales: number;
  total_right_sales: number;
  total_sales: number;
}

// ダウンラインレスポンス
export interface DownlineResponse {
  target_member: OrganizationNode;
  downline_tree: OrganizationNode[];
  downline_count: number;
}

// CSV出力レスポンス
export interface CsvExportResponse {
  filename: string;
  content: string;
  format: string;
}

export class OrganizationService {
  private static readonly BASE_URL = '/v1/organization';

  /**
   * 組織ツリー取得
   */
  static async getOrganizationTree(
    memberId?: number,
    maxLevel?: number
  ): Promise<OrganizationTree> {
    const params: any = {};
    if (memberId !== undefined) params.member_id = memberId;
    if (maxLevel !== undefined) params.max_level = maxLevel;
    
    return ApiService.get<OrganizationTree>(`${this.BASE_URL}/tree`, { params });
  }

  /**
   * 組織統計取得
   */
  static async getOrganizationStats(): Promise<OrganizationStats> {
    return ApiService.get<OrganizationStats>(`${this.BASE_URL}/stats`);
  }

  /**
   * 特定メンバーのダウンライン取得
   */
  static async getMemberDownline(
    memberNumber: string,
    maxDepth: number = 10
  ): Promise<DownlineResponse> {
    return ApiService.get<DownlineResponse>(
      `${this.BASE_URL}/member/${memberNumber}/downline`,
      { params: { max_depth: maxDepth } }
    );
  }

  /**
   * 組織図CSV出力
   */
  static async exportOrganizationCsv(
    formatType: 'binary' | 'referral' = 'binary'
  ): Promise<CsvExportResponse> {
    return ApiService.get<CsvExportResponse>(
      `${this.BASE_URL}/export/csv`,
      { params: { format_type: formatType } }
    );
  }

  /**
   * CSVファイルダウンロード
   */
  static async downloadCsv(formatType: 'binary' | 'referral' = 'binary'): Promise<void> {
    try {
      const response = await this.exportOrganizationCsv(formatType);
      
      // CSVファイルをダウンロード
      const blob = new Blob([response.content], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      
      if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', response.filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('CSV出力エラー:', error);
      throw error;
    }
  }

  /**
   * 組織ノードの検索
   */
  static searchNodes(nodes: OrganizationNode[], searchTerm: string): OrganizationNode[] {
    const results: OrganizationNode[] = [];
    
    const search = (nodeList: OrganizationNode[]) => {
      for (const node of nodeList) {
        // 会員番号、氏名、称号で検索
        if (
          node.member_number.includes(searchTerm) ||
          node.name.includes(searchTerm) ||
          node.title.includes(searchTerm)
        ) {
          results.push(node);
        }
        
        // 子ノードも検索
        if (node.children.length > 0) {
          search(node.children);
        }
      }
    };
    
    search(nodes);
    return results;
  }

  /**
   * 特定レベルでのフィルタリング
   */
  static filterByLevel(nodes: OrganizationNode[], level: number): OrganizationNode[] {
    const results: OrganizationNode[] = [];
    
    const filter = (nodeList: OrganizationNode[]) => {
      for (const node of nodeList) {
        if (node.level === level) {
          results.push(node);
        }
        
        // 子ノードもフィルタリング
        if (node.children.length > 0) {
          filter(node.children);
        }
      }
    };
    
    filter(nodes);
    return results;
  }

  /**
   * ノードの展開/折りたたみ状態を更新
   */
  static toggleNodeExpansion(nodes: OrganizationNode[], nodeId: string): OrganizationNode[] {
    const toggle = (nodeList: OrganizationNode[]): OrganizationNode[] => {
      return nodeList.map(node => {
        if (node.id === nodeId) {
          return { ...node, is_expanded: !node.is_expanded };
        }
        if (node.children.length > 0) {
          return { ...node, children: toggle(node.children) };
        }
        return node;
      });
    };
    
    return toggle(nodes);
  }

  /**
   * 組織の深度を計算
   */
  static calculateDepth(nodes: OrganizationNode[]): number {
    let maxDepth = 0;
    
    const calculateNodeDepth = (nodeList: OrganizationNode[], currentDepth: number = 0) => {
      for (const node of nodeList) {
        maxDepth = Math.max(maxDepth, currentDepth);
        if (node.children.length > 0) {
          calculateNodeDepth(node.children, currentDepth + 1);
        }
      }
    };
    
    calculateNodeDepth(nodes);
    return maxDepth;
  }

  /**
   * 組織の総メンバー数を計算
   */
  static countTotalMembers(nodes: OrganizationNode[]): number {
    let count = 0;
    
    const countNodes = (nodeList: OrganizationNode[]) => {
      for (const node of nodeList) {
        count++;
        if (node.children.length > 0) {
          countNodes(node.children);
        }
      }
    };
    
    countNodes(nodes);
    return count;
  }

  /**
   * ステータス別の色を取得
   */
  static getStatusColor(status: string): 'success' | 'warning' | 'error' | 'default' {
    switch (status.toUpperCase()) {
      case 'ACTIVE':
        return 'success';
      case 'INACTIVE':
        return 'warning';
      case 'WITHDRAWN':
        return 'error';
      default:
        return 'default';
    }
  }

  /**
   * 称号の色を取得
   */
  static getTitleColor(title: string): string {
    if (title.includes('エンペラー') || title.includes('エンブレス')) return '#8b5cf6';
    if (title.includes('キング') || title.includes('クイーン')) return '#3b82f6';
    if (title.includes('ロード') || title.includes('レディ')) return '#10b981';
    if (title.includes('ナイト') || title.includes('デイム')) return '#f59e0b';
    if (title.includes('エリアディレクター')) return '#8b5cf6';
    if (title.includes('ディレクター')) return '#3b82f6';
    if (title.includes('マネージャー')) return '#10b981';
    if (title.includes('リーダー')) return '#f59e0b';
    return '#6b7280';
  }
}
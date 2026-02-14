import React, { useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Progress,
  Table,
  Tag,
  Space,
  Button,
  Alert,
  Spin,
} from 'antd';
import {
  NetworkOutlined,
  SecurityScanOutlined,
  CloudServerOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { Line, Pie, Column } from '@ant-design/plots';
import { useQuery } from '@tanstack/react-query';
import { useWebSocket } from '../../hooks/useWebSocket';
import { dashboardService } from '../../services/dashboard';
import { formatNumber, formatBytes, getSeverityColor } from '../../utils/formatters';

const Dashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState('24h');
  const { lastMessage, sendMessage } = useWebSocket('/network/realtime');

  // Fetch dashboard data
  const {
    data: dashboardData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['dashboard', timeRange],
    queryFn: () => dashboardService.getDashboardData(timeRange),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch alerts
  const {
    data: alerts,
    isLoading: alertsLoading,
  } = useQuery({
    queryKey: ['alerts'],
    queryFn: dashboardService.getAlerts(),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  useEffect(() => {
    if (lastMessage) {
      // Handle real-time updates
      const data = JSON.parse(lastMessage.data);
      console.log('Real-time update:', data);
      refetch();
    }
  }, [lastMessage, refetch]);

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error loading dashboard"
        description="Failed to load dashboard data. Please try again."
        type="error"
        showIcon
        action={
          <Button size="small" onClick={() => refetch()}>
            Retry
          </Button>
        }
      />
    );
  }

  const stats = dashboardData?.stats || {};
  const networkMetrics = dashboardData?.networkMetrics || [];
  const securityEvents = dashboardData?.securityEvents || [];
  const infrastructureStatus = dashboardData?.infrastructureStatus || [];

  // Network traffic chart config
  const networkTrafficConfig = {
    data: networkMetrics,
    xField: 'time',
    yField: 'value',
    seriesField: 'type',
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
  };

  // Security events pie chart config
  const securityEventsConfig = {
    data: securityEvents,
    angleField: 'value',
    colorField: 'category',
    radius: 0.8,
    label: {
      type: 'outer',
      content: '{name} {percentage}',
    },
  };

  // Infrastructure status column config
  const infrastructureColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = getSeverityColor(status);
        const icon = status === 'healthy' ? <CheckCircleOutlined /> :
                    status === 'warning' ? <ExclamationCircleOutlined /> :
                    <CloseCircleOutlined />;
        return <Tag color={color} icon={icon}>{status}</Tag>;
      },
    },
    {
      title: 'CPU Usage',
      dataIndex: 'cpuUsage',
      key: 'cpuUsage',
      render: (usage: number) => (
        <Progress percent={usage} size="small" status={usage > 80 ? 'exception' : 'normal'} />
      ),
    },
    {
      title: 'Memory Usage',
      dataIndex: 'memoryUsage',
      key: 'memoryUsage',
      render: (usage: number) => (
        <Progress percent={usage} size="small" status={usage > 80 ? 'exception' : 'normal'} />
      ),
    },
  ];

  // Recent alerts table columns
  const alertColumns = [
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => {
        const color = getSeverityColor(severity);
        return <Tag color={color}>{severity.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Source',
      dataIndex: 'source',
      key: 'source',
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
    },
  ];

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={18}>
          <h2>Network Operations Center Dashboard</h2>
        </Col>
        <Col span={6} style={{ textAlign: 'right' }}>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetch()}
              loading={isLoading}
            >
              Refresh
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Devices"
              value={stats.totalDevices || 0}
              prefix={<NetworkOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Online Devices"
              value={stats.onlineDevices || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={`/ ${stats.totalDevices || 0}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Security Events"
              value={stats.securityEvents || 0}
              prefix={<SecurityScanOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Infrastructure Health"
              value={stats.infrastructureHealth || 0}
              suffix="%"
              prefix={<CloudServerOutlined />}
              valueStyle={{ 
                color: (stats.infrastructureHealth || 0) > 80 ? '#52c41a' : '#fa8c16' 
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts Row */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={16}>
          <Card title="Network Traffic" extra={<Button size="small">24h</Button>}>
            <Line {...networkTrafficConfig} height={300} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Security Events by Category">
            <Pie {...securityEventsConfig} height={300} />
          </Card>
        </Col>
      </Row>

      {/* Tables Row */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Infrastructure Status" extra={<Button size="small">View All</Button>}>
            <Table
              columns={infrastructureColumns}
              dataSource={infrastructureStatus}
              pagination={{ pageSize: 5, size: 'small' }}
              size="small"
              scroll={{ y: 300 }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Recent Alerts" extra={<Button size="small">View All</Button>}>
            <Table
              columns={alertColumns}
              dataSource={alerts?.slice(0, 5)}
              pagination={false}
              size="small"
              scroll={{ y: 300 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;

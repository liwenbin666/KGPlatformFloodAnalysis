/**
 *
 */
package com.DataStructTransfer;

import java.io.IOException;
import java.text.DecimalFormat;
import java.util.GregorianCalendar;
import java.util.Vector;

import com.DataStructTransfer.SpatialAggregation.SpatialDataType;
import com.EstimationMethods.MomentAlg;
import com.PubUsedClasses.RSTime;
import com.TrendAnalysisMethods.SPTAAlg;
import com.logicdoc.IOClasses.IOTxtFile;

/**
 * @author lenovo
 * ���뷴�ȼ�Ȩ��ֵ����������������
 */
public class IDW {
    public enum InterpolationDataType {Precipitation,PET,TMean,Runoff};

    private InterpolationDataType m_InterpDataType = null;
    private RSTime.RSTimeType m_InterpDataTimeType = null;
    private int m_refStaNum = 3; //��֤վ��Ŀ

    private double m_invalidVal = -99;
    private GregorianCalendar m_dataBegCale = null;
    private GregorianCalendar m_dataEndCale = null;
    private String[][] m_TargetIDArr = null; //���У��ֱ�Ϊ����ֵĿ��վ�����վ��,����,��γ
    private String[][] m_ObsIDArr = null; //���У��ֱ�Ϊ���۲�վ�����վ��,����,��γ����վ�ű���������

    private double[][] m_dataArrOri = null; //����ֵ���� ��:�������˳������;����Ϊ���;���ݴ����Ӧ����˳��һ��;Ҫ�����ݴ���ʼʱ��������ʱ��������ȱ��
    private double[][] m_dataArrNew = null;


    /**
     * @param argsw qishi
     */
    public static void main(String[] args) {
        // TODO Auto-generated method stub
        try {
            long TotalstartTime = System.currentTimeMillis();
            long startTime = System.currentTimeMillis();
//			System.out.println("��ʼ��"+(i+1)+"/323����ˮ");
            IDW IDWInterp = new IDW();
            if (!IDWInterp.calc()) {
                System.out.println("Failure");
                return;
            } else {
                String outputFileName = "../datas/areadata/res.txt";
                IDWInterp.writeDataArrNewToTxt(outputFileName);
                System.out.println("Success");
                long endTime = System.currentTimeMillis();
                System.out.println("������ˮ��ʱ��"+(endTime - startTime)/1000.0 + "s");
                System.out.println("����ʱ��"+(endTime - TotalstartTime)/1000.0 + "s");
            }
//			for(int i=0;i<323;i++)
////			for(int i=0;i<3;i++)
//			{
//				long startTime = System.currentTimeMillis();
//				System.out.println("��ʼ��"+(i+1)+"/323����ˮ");
//				IDW2 IDWInterp = new IDW2(i);
//				if (!IDWInterp.calc()) {
//					System.out.println("Failure");
//					return;
//				} else {
//					String outputFileName = "/doc/����ļ�/IDWInterpolation/res"+i+".txt";
//					IDWInterp.writeDataArrNewToTxt(outputFileName);
//					System.out.println("Success");
//					long endTime = System.currentTimeMillis();
//					System.out.println("������ˮ��ʱ��"+(endTime - startTime)/1000.0 + "s");
//					System.out.println("����ʱ��"+(endTime - TotalstartTime)/1000.0 + "s");
//				}
//			}
        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }

    public IDW() throws IOException {
        this.initialize();
    }

    private void initialize() throws IOException {
        IOTxtFile IOFile = new IOTxtFile();
        double[][] res = IOFile.readData("../datas/areadata/conf.txt", 1);
        int longlen=(int)res[0].length;
//		System.out.println(res[0][11]);
        int tempInt = (int)res[0][0];
        m_InterpDataType = this.getInterpDataTypeFromVal(tempInt);
        tempInt = (int)res[0][1];
        m_InterpDataTimeType = RSTime.RSTimeType.getTimeType(tempInt);
        m_refStaNum = (int)res[0][2];
        m_invalidVal = res[0][3];

        int year = (int)res[0][4];
        int month = (int)res[0][5];
        int day = (int)res[0][6];
        int hour =(int)res[0][7];
        int minute =(int)res[0][8];
        m_dataBegCale = new GregorianCalendar(year,month-1,day,hour,minute);
        year = (int)res[0][9];
        month = (int)res[0][10];
        day = (int)res[0][11];
        hour =(int)res[0][12];
        minute =(int)res[0][13];
        m_dataEndCale = new GregorianCalendar(year,month-1,day,hour,minute);

        m_TargetIDArr = IOFile.readStrData("../datas/areadata/TargetID.txt", 1);
        m_ObsIDArr = IOFile.readStrData("../datas/areadata/ObsID.txt", 1);
//		System.out.println(m_InterpDataType);
//		System.out.println(InterpolationDataType.Precipitation);
        String dataOriFileName = "";
        if (m_InterpDataType == InterpolationDataType.Precipitation) {
//			dataOriFileName = "Precipitations/Precipitation"+floodnum+".txt";
            dataOriFileName = "Precipitation.txt";
        } else if (m_InterpDataType == InterpolationDataType.PET) {
            dataOriFileName = "PET.txt";
        } else if (m_InterpDataType == InterpolationDataType.TMean) {
            dataOriFileName = "TMean.txt";
        } else if (m_InterpDataType == InterpolationDataType.Runoff) {
            dataOriFileName = "Runoff.txt";
        }
        dataOriFileName = "../datas/areadata/" + dataOriFileName;
        m_dataArrOri = IOFile.readData(dataOriFileName, 0);
//		System.out.println(m_dataArrOri[29][13]);
//		System.out.println(m_dataArrOri[30][13]);
//		System.out.println(m_dataArrOri[31][13]);
    }

    public boolean calc() {
        int i,j,k;

        int begYear = m_dataBegCale.get(GregorianCalendar.YEAR);
        int endYear = m_dataEndCale.get(GregorianCalendar.YEAR);

        int rowNum = 0;
        if (m_InterpDataTimeType == RSTime.RSTimeType.RSYear) {
            rowNum = endYear - begYear + 1;
        } else if (m_InterpDataTimeType == RSTime.RSTimeType.RSMonth) {
            rowNum = (endYear - begYear + 1) * 12;
        } else if (m_InterpDataTimeType == RSTime.RSTimeType.RSHour) {
            rowNum =RSTime.getTimeInterval(m_dataBegCale,m_dataEndCale,RSTime.RSTimeType.RSHour, 1);
        }
        //ֱ�ӹ涨����
        rowNum = m_dataArrOri.length-1;
        if (rowNum != m_dataArrOri.length-1) {
            System.out.println("����ֵ���ݳ�����ʼĩʱ�����ò���");
            System.out.println(rowNum);
            System.out.println(m_dataArrOri.length-1);

            return false;
        }
//

        int colNum = m_TargetIDArr.length;
        System.out.println("rowNum");
        System.out.println(rowNum);
        System.out.println("colNum");
        System.out.println(colNum);
        m_dataArrNew = new double[rowNum][colNum];


        int targetIDNum = m_TargetIDArr.length;
        int obsIDNum = m_ObsIDArr.length;
        for (i=0; i<targetIDNum; i++) { //��ֵĿ���ѭ��
//			System.out.println(i);
            double XTarget = Double.valueOf(m_TargetIDArr[i][1]); //��ֵĿ���Ķ���
            double YTarget = Double.valueOf(m_TargetIDArr[i][2]); //��ֵĿ���ı�γ
            double[] distanceArr = new double[obsIDNum]; //��Ź۲�����ֵĿ���ľ���
            for (j=0; j<obsIDNum; j++) {
                double XObs = Double.valueOf(m_ObsIDArr[j][1]); //�۲��Ķ���
                double YObs = Double.valueOf(m_ObsIDArr[j][2]); //�۲��ı�γ
                distanceArr[j] = (XObs-XTarget)*(XObs-XTarget) + (YObs-YTarget)*(YObs-YTarget);
                distanceArr[j] = Math.sqrt(distanceArr[j]);
            }
            int[] disRankArr = SPTAAlg.calcRankSer(distanceArr);
            double[][] arrForInterp = new double[rowNum+1][m_refStaNum]; //��Ŵ���ֵ��������,���д�ž���
            for (j=0; j<m_refStaNum; j++) {
                int rank = j+1;
                int selectObsIdx = this.findObsIdx(disRankArr, rank);
                if (selectObsIdx == -99) { //��ʱ����disRankArr�����ظ����ֵ��Ⱥţ���rank-1����������
                    selectObsIdx = this.findObsIdx(disRankArr, rank-1);
                }
                double selectObsID = Double.valueOf(m_ObsIDArr[selectObsIdx][0]);
                double[] tempArr = this.findSelectDataArr(selectObsID);
                arrForInterp[0][j] = distanceArr[selectObsIdx];
                for (k=0; k<rowNum; k++) {
                    arrForInterp[k+1][j] = tempArr[k];
//
//					System.out.println("arrForInterp[k+1][j]");
//					System.out.println(arrForInterp[k+1][j]);
                }

            }

            for (k=0; k<rowNum; k++) {
                //ʱ��ѭ��
                Vector<Double> validValVec = new Vector<Double>();
                Vector<Double> validDistanceVec = new Vector<Double>();
                for (j=0; j<m_refStaNum; j++) {
                    double distance = arrForInterp[0][j];
                    double val = arrForInterp[k+1][j];
                    if (val != m_invalidVal) {
                        validValVec.add(val);
//						System.out.println("val");
//						System.out.println(val);
                        validDistanceVec.add(distance);
                    }
                }
                int validDataSize = validValVec.size();
                if (validDataSize == 0) {
//					System.out.println("�ڵ�"+(i+1)+"����ֵĿ����"+(k+1)+"��ʱ��˳λû���㹻����Чֵ����ֵʹ��");
//					return false;
                    m_dataArrNew[k][i] = -99;
                    continue;
                }
                double sum1 = 0, sum2 = 0;
                for (j=0; j<validDataSize; j++) {
                    double temp1 = validDistanceVec.get(j);
                    temp1 = Math.pow(temp1, -2.0f);
                    sum2 += temp1;

                    double temp2 = validValVec.get(j);
                    temp2 = temp2 * temp1;
                    sum1 += temp2;
                }
//				System.out.println("sum1");
//				System.out.println(sum1);
//				System.out.println("sum2");
//				System.out.println(sum2);
                m_dataArrNew[k][i] = sum1 / sum2;
            }
        }
//		m_dataArrNew = new double[rowNum][colNum];
//		for (i=0;i<rowNum;i++)
//		{
//			for (j=0;j<colNum;j++)
//				if (m_dataArrNew[i][j]!=0.00)
//				{System.out.println(m_dataArrNew[i][j]);
//					return true;
//				}
//		}

        return true;
    }

    //�Ӵ���ֵ����m_dataArrOri���ҵ�ָ����վ��refObsID������
    private double[] findSelectDataArr(double refObsID) {
//		String refObsID1=String.valueOf(refObsID);
//		System.out.println("refObsID");
//		System.out.println(refObsID1);


//		System.out.println("m_dataArrOri[0][0]");
//		System.out.println(m_dataArrOri[0][0]);
        int i, j;
        int length = m_dataArrOri.length-1;
        double[] res = new double[length];
//		System.out.println("m_dataArrOri[0].length");
//		System.out.println(m_dataArrOri[0].length);
        for (j=0; j<m_dataArrOri[0].length; j++) {
            double obsID = m_dataArrOri[0][j];
//			System.out.println("obsID");
//			System.out.println(obsID);
            if (obsID == refObsID) {
                for (i=1; i<length+1; i++) {
                    res[i-1] = m_dataArrOri[i][j];
//					System.out.println("res");
//					System.out.println(res[i-1]);
                }
                break;
            }
        }

        return res;
    }

    //��disRankArr���ҵ�ָ��rank�����б��
    private int findObsIdx(int[] disRankArr, int rank) {
        int idx = -99;
        int i;
        for (i=0; i<disRankArr.length; i++) {
            if (disRankArr[i] == rank) {
                idx = i;
                break;
            }
        }

        return idx;
    }

    private InterpolationDataType getInterpDataTypeFromVal(int val) {
        InterpolationDataType res = null;
        if (val == 1) {
            res = InterpolationDataType.Precipitation;
        } else if (val == 2) {
            res = InterpolationDataType.PET;
        } else if (val == 3) {
            res = InterpolationDataType.TMean;
        } else if (val == 4) {
            res = InterpolationDataType.Runoff;
        }
        return res;
    }

    public void writeDataArrNewToTxt(String fileName) throws IOException {
        String Title = "";

        IOTxtFile file = new IOTxtFile();
        file.writeArrToTXT(fileName, Title, this.m_dataArrNew, new DecimalFormat("#0.00"));
    }
}


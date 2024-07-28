### 概述

- **目的**：利用距离反比加权插值法，根据气象站观测数据生成网格数据。
- 主要类和方法：
  - `IDW2`：实现IDW方法的主要类。
  - `main`：主方法，用于执行插值操作。

### 主要部分解析

#### 类定义和成员变量

```java
public class IDW2 {
    public enum InterpolationDataType {Precipitation, PET, TMean, Runoff};
    private InterpolationDataType m_InterpDataType = null;
    private RSTime.RSTimeType m_InterpDataTimeType = null;
    private int m_refStaNum = 3;
    private double m_invalidVal = -99;
    private GregorianCalendar m_dataBegCale = null;
    private GregorianCalendar m_dataEndCale = null;
    private String[][] m_TargetIDArr = null;
    private String[][] m_ObsIDArr = null;
    private double[][] m_dataArrOri = null;
    private double[][] m_dataArrNew = null;
```

- `InterpolationDataType`：枚举类型，定义插值数据类型（降水、蒸发、平均温度、径流）。
- `m_InterpDataType`：插值数据类型。
- `m_InterpDataTimeType`：插值数据时间类型。
- `m_refStaNum`：参考站数量。
- `m_invalidVal`：无效值标志。
- `m_dataBegCale` 和 `m_dataEndCale`：数据起始和结束时间。
- `m_TargetIDArr` 和 `m_ObsIDArr`：目标站点和观测站点信息。
- `m_dataArrOri` 和 `m_dataArrNew`：原始数据和插值后的新数据。

#### 主方法

```java
public static void main(String[] args) {
    try {
        long TotalstartTime = System.currentTimeMillis();
        IDW2 IDWInterp = new IDW2();
        if (!IDWInterp.calc()) {
            System.out.println("Failure");
            return;
        } else {
            String outputFileName = "/doc/输出文件/IDWInterpolation/res.txt";
            IDWInterp.writeDataArrNewToTxt(outputFileName);
            System.out.println("Success");
            long endTime = System.currentTimeMillis();
            System.out.println("总用时："+(endTime - TotalstartTime)/1000.0 + "s");
        }
    } catch (IOException e) {
        e.printStackTrace();
    }
}
```

- **主方法**：初始化IDW2对象并执行插值计算。如果计算成功，则将结果写入文件。

  res.txt有误，表明中间的插值过程有问题

#### 构造方法和初始化

```java
public IDW2() throws IOException {
    this.initialize();
}

private void initialize() throws IOException {
    IOTxtFile IOFile = new IOTxtFile();
    double[][] res = IOFile.readData("/doc/输入文件/IDWInterpolation/conf.txt", 1);
    int tempInt = (int)res[0][0];
    m_InterpDataType = this.getInterpDataTypeFromVal(tempInt);
    tempInt = (int)res[0][1];
    m_InterpDataTimeType = RSTime.RSTimeType.getTimeType(tempInt);
    m_refStaNum = (int)res[0][2];
    m_invalidVal = res[0][3];

    int year = (int)res[0][4];
    int month = (int)res[0][5];
    int day = (int)res[0][6];
    int hour = (int)res[0][7];
    int minute = (int)res[0][8];
    m_dataBegCale = new GregorianCalendar(year, month-1, day, hour, minute);
    year = (int)res[0][9];
    month = (int)res[0][10];
    day = (int)res[0][11];
    hour = (int)res[0][12];
    minute = (int)res[0][13];
    m_dataEndCale = new GregorianCalendar(year, month-1, day, hour, minute);

    m_TargetIDArr = IOFile.readStrData("/doc/输入文件/IDWInterpolation/TargetID.txt", 1);
    m_ObsIDArr = IOFile.readStrData("/doc/输入文件/IDWInterpolation/ObsID.txt", 1);

    String dataOriFileName = "";
    if (m_InterpDataType == InterpolationDataType.Precipitation) {
        dataOriFileName = "Precipitation.txt";
    } else if (m_InterpDataType == InterpolationDataType.PET) {
        dataOriFileName = "PET.txt";
    } else if (m_InterpDataType == InterpolationDataType.TMean) {
        dataOriFileName = "TMean.txt";    
    } else if (m_InterpDataType == InterpolationDataType.Runoff) {
        dataOriFileName = "Runoff.txt";    
    }
    dataOriFileName = "/doc/输入文件/IDWInterpolation/" + dataOriFileName;
    m_dataArrOri = IOFile.readData(dataOriFileName, 0);
}
```

- **初始化方法**：从配置文件中读取参数并初始化类成员变量，包括数据类型、时间类型、参考站数量、无效值标志、数据起始和结束时间、目标站点和观测站点信息等。

  ![image-20240611205329516](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20240611205329516.png)

  TargetID:如下——正确

  ![image-20240611205828739](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20240611205828739.png)

  ObsID:如下——为空——已解决

  ![image-20240611210011444](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20240611210011444.png)

  原始降雨数据文件：如下——正确

  ![image-20240613152447155](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20240613152447155.png)

- 这段代码实现了`IDW2`类的构造方法和初始化方法，其中通过读取配置文件和数据文件来初始化插值所需的各种参数。下面对这段代码进行详细解析。

  ### 构造方法

  ```
  public IDW2() throws IOException {
      this.initialize();
  }
  ```

  - 构造方法`IDW2`调用了初始化方法`initialize`，用于初始化类的成员变量。由于初始化过程中可能涉及文件读取操作，因此声明了`throws IOException`以处理可能的输入输出异常。

  ### 初始化方法

  ```
  private void initialize() throws IOException {
      IOTxtFile IOFile = new IOTxtFile();
  ```

  - 创建`IOTxtFile`对象，用于读取配置文件和数据文件。

  #### 读取配置文件

  ```
      double[][] res = IOFile.readData("/doc/输入文件/IDWInterpolation/conf.txt", 1);
  ```

  - 读取配置文件`conf.txt`，并将其内容存储在二维数组`res`中。

  #### 初始化插值数据类型和时间类型

  ```
      int tempInt = (int)res[0][0];
      m_InterpDataType = this.getInterpDataTypeFromVal(tempInt);
      tempInt = (int)res[0][1];
      m_InterpDataTimeType = RSTime.RSTimeType.getTimeType(tempInt);
  ```

  - 根据配置文件中的值初始化插值数据类型`m_InterpDataType`和插值数据时间类型`m_InterpDataTimeType`。使用辅助方法`getInterpDataTypeFromVal`将整数转换为枚举类型。

  #### 初始化参考站数量和无效值标志

  ```
      m_refStaNum = (int)res[0][2];
      m_invalidVal = res[0][3];
  ```

  - 从配置文件中读取参考站数量`m_refStaNum`和无效值标志`m_invalidVal`。

  #### 初始化时间范围

  ```
      int year = (int)res[0][4];
      int month = (int)res[0][5];
      int day = (int)res[0][6];
      int hour = (int)res[0][7];
      int minute = (int)res[0][8];
      m_dataBegCale = new GregorianCalendar(year, month-1, day, hour, minute);
      year = (int)res[0][9];
      month = (int)res[0][10];
      day = (int)res[0][11];
      hour = (int)res[0][12];
      minute = (int)res[0][13];
      m_dataEndCale = new GregorianCalendar(year, month-1, day, hour, minute);
  ```

  - 从配置文件中读取起始时间和结束时间，并使用`GregorianCalendar`对象`m_dataBegCale`和`m_dataEndCale`进行初始化。月份参数减一是因为Java的月份是从0开始计数的。

  #### 读取目标站点和观测站点信息

  ```
      m_TargetIDArr = IOFile.readStrData("/doc/输入文件/IDWInterpolation/TargetID.txt", 1);
      m_ObsIDArr = IOFile.readStrData("/doc/输入文件/IDWInterpolation/ObsID.txt", 1);
  ```

  - 读取目标站点和观测站点的ID信息，分别存储在二维字符串数组`m_TargetIDArr`和`m_ObsIDArr`中。

  #### 根据数据类型选择数据文件

  ```
      String dataOriFileName = "";
      if (m_InterpDataType == InterpolationDataType.Precipitation) {
          dataOriFileName = "Precipitation.txt";
      } else if (m_InterpDataType == InterpolationDataType.PET) {
          dataOriFileName = "PET.txt";
      } else if (m_InterpDataType == InterpolationDataType.TMean) {
          dataOriFileName = "TMean.txt";    
      } else if (m_InterpDataType == InterpolationDataType.Runoff) {
          dataOriFileName = "Runoff.txt";    
      }
      dataOriFileName = "/doc/输入文件/IDWInterpolation/" + dataOriFileName;
      m_dataArrOri = IOFile.readData(dataOriFileName, 0);
  ```

  - 根据插值数据类型选择相应的数据文件名，并读取该数据文件的内容存储在二维数组`m_dataArrOri`中。

  ### 辅助方法

  这段代码中还涉及了一些辅助方法，例如`getInterpDataTypeFromVal`，用于将整数值转换为对应的枚举类型。这些方法在类的其他部分中定义和实现。

  ### 总结

  通过初始化方法，`IDW2`类从配置文件中读取并设置了插值计算所需的各种参数，包括插值数据类型、时间类型、参考站数量、无效值标志、时间范围、目标站点和观测站点信息以及原始观测数据。这样，`IDW2`类便准备好了进行距离反比加权插值计算。

#### 插值计算方法

```java
public boolean calc() {
    int begYear = m_dataBegCale.get(GregorianCalendar.YEAR);
    int endYear = m_dataEndCale.get(GregorianCalendar.YEAR);

    int rowNum = m_dataArrOri.length - 1;
    int colNum = m_TargetIDArr.length;
    m_dataArrNew = new double[rowNum][colNum];

    int targetIDNum = m_TargetIDArr.length;
    int obsIDNum = m_ObsIDArr.length;
    for (int i = 0; i < targetIDNum; i++) {
        double XTarget = Double.valueOf(m_TargetIDArr[i][1]);
        double YTarget = Double.valueOf(m_TargetIDArr[i][2]);
        double[] distanceArr = new double[obsIDNum];
        for (int j = 0; j < obsIDNum; j++) {
            double XObs = Double.valueOf(m_ObsIDArr[j][1]);
            double YObs = Double.valueOf(m_ObsIDArr[j][2]);
            distanceArr[j] = Math.sqrt(Math.pow(XObs - XTarget, 2) + Math.pow(YObs - YTarget, 2));
        }
        int[] disRankArr = SPTAAlg.calcRankSer(distanceArr);
        double[][] arrForInterp = new double[rowNum + 1][m_refStaNum];
        for (int j = 0; j < m_refStaNum; j++) {
            int rank = j + 1;
            int selectObsIdx = this.findObsIdx(disRankArr, rank);
            if (selectObsIdx == -99) {
                selectObsIdx = this.findObsIdx(disRankArr, rank - 1);
            }
            double selectObsID = Double.valueOf(m_ObsIDArr[selectObsIdx][0]);
            double[] tempArr = this.findSelectDataArr(selectObsID);
            arrForInterp[0][j] = distanceArr[selectObsIdx];
            for (int k = 0; k < rowNum; k++) {
                arrForInterp[k + 1][j] = tempArr[k];
            }
        }

        for (int k = 0; k < rowNum; k++) {
            Vector<Double> validValVec = new Vector<Double>();
            Vector<Double> validDistanceVec = new Vector<Double>();
            for (int j = 0; j < m_refStaNum; j++) {
                double distance = arrForInterp[0][j];
                double val = arrForInterp[k + 1][j];
                if (val != m_invalidVal) {
                    validValVec.add(val);
                    validDistanceVec.add(distance);
                }
            }
            int validDataSize = validValVec.size();
            if (validDataSize == 0) {
                m_dataArrNew[k][i] = -99;
                continue;
            }
            double sum1 = 0, sum2 = 0;
            for (int j = 0; j < validDataSize; j++) {
                double temp1 = Math.pow(validDistanceVec.get(j), -2.0);
                sum2 += temp1;
                sum1 += validValVec.get(j) * temp1;
            }
            m_dataArrNew[k][i] = sum1 / sum2;
        }
    }
    return true;
}
```

- **插值计算**：计算目标站点与观测站点之间的距离，选择最近的参考站，使用距离的倒数加权求和计算插值结果。

- 这段代码实现了`IDW2`类中的插值计算方法`calc`。该方法使用反距离加权插值法（IDW）计算目标点的插值值。下面是对该方法的详细解析。

  ### 方法签名

  ```
  public boolean calc() {
  ```

  - 方法`calc`的返回类型是布尔值`boolean`，用于指示计算是否成功。

  ### 初始化变量

  ```
      int begYear = m_dataBegCale.get(GregorianCalendar.YEAR);
      int endYear = m_dataEndCale.get(GregorianCalendar.YEAR);
  
      int rowNum = m_dataArrOri.length - 1;
      int colNum = m_TargetIDArr.length;
      m_dataArrNew = new double[rowNum][colNum];
  ```

  - 通过获取`GregorianCalendar`对象中的年份，初始化起始年份和结束年份。
  - `rowNum`表示原始数据行数减一（因为通常第一行是表头）。
  - `colNum`表示目标点的数量。
  - 初始化`m_dataArrNew`数组，用于存储插值结果。

  ### 计算每个目标点的插值值

  ```
      int targetIDNum = m_TargetIDArr.length;
      int obsIDNum = m_ObsIDArr.length;
      for (int i = 0; i < targetIDNum; i++) {
          double XTarget = Double.valueOf(m_TargetIDArr[i][1]);
          double YTarget = Double.valueOf(m_TargetIDArr[i][2]);
          double[] distanceArr = new double[obsIDNum];
  ```

  - `targetIDNum`表示目标点的数量。
  - `obsIDNum`表示观测点的数量。
  - 循环遍历每个目标点，获取目标点的坐标，并初始化一个数组`distanceArr`来存储每个观测点与当前目标点之间的距离。

  #### 计算目标点到每个观测点的距离

  ```
          for (int j = 0; j < obsIDNum; j++) {
              double XObs = Double.valueOf(m_ObsIDArr[j][1]);
              double YObs = Double.valueOf(m_ObsIDArr[j][2]);
              distanceArr[j] = Math.sqrt(Math.pow(XObs - XTarget, 2) + Math.pow(YObs - YTarget, 2));
          }
  ```

  - 循环遍历每个观测点，计算观测点与当前目标点之间的欧几里得距离，并存储在`distanceArr`中。

  #### 计算距离排名并选择最近的观测点

  ```
          int[] disRankArr = SPTAAlg.calcRankSer(distanceArr);
          double[][] arrForInterp = new double[rowNum + 1][m_refStaNum];
          for (int j = 0; j < m_refStaNum; j++) {
              int rank = j + 1;
              int selectObsIdx = this.findObsIdx(disRankArr, rank);
              if (selectObsIdx == -99) {
                  selectObsIdx = this.findObsIdx(disRankArr, rank - 1);
              }
              double selectObsID = Double.valueOf(m_ObsIDArr[selectObsIdx][0]);
              double[] tempArr = this.findSelectDataArr(selectObsID);
              arrForInterp[0][j] = distanceArr[selectObsIdx];
              for (int k = 0; k < rowNum; k++) {
                  arrForInterp[k + 1][j] = tempArr[k];
              }
          }
  ```

  - 使用`SPTAAlg.calcRankSer`方法计算距离的排名数组`disRankArr`。
  - 初始化二维数组`arrForInterp`，用于存储选择的观测点及其距离和数据值。
  - 循环选择距离最近的观测点，并确保选择的观测点有效。
  - 将选择的观测点的距离和数据值存储到`arrForInterp`中。

  ### 插值计算

  ```
          for (int k = 0; k < rowNum; k++) {
              Vector<Double> validValVec = new Vector<Double>();
              Vector<Double> validDistanceVec = new Vector<Double>();
              for (int j = 0; j < m_refStaNum; j++) {
                  double distance = arrForInterp[0][j];
                  double val = arrForInterp[k + 1][j];
                  if (val != m_invalidVal) {
                      validValVec.add(val);
                      validDistanceVec.add(distance);
                  }
              }
              int validDataSize = validValVec.size();
              if (validDataSize == 0) {
                  m_dataArrNew[k][i] = -99;
                  continue;
              }
              double sum1 = 0, sum2 = 0;
              for (int j = 0; j < validDataSize; j++) {
                  double temp1 = Math.pow(validDistanceVec.get(j), -2.0);
                  sum2 += temp1;
                  sum1 += validValVec.get(j) * temp1;
              }
              m_dataArrNew[k][i] = sum1 / sum2;
          }
      }
      return true;
  }
  ```

  - 对每一行数据进行插值计算。
  - 使用向量`validValVec`和`validDistanceVec`存储有效的观测值和对应的距离。
  - 如果没有有效数据，插值结果设置为-99。
  - 否则，使用反距离加权公式计算插值值，并存储在`m_dataArrNew`中。

  ### 总结

  这段代码实现了反距离加权插值算法的核心部分，通过遍历每个目标点并计算与观测点的距离，选择最近的几个观测点进行加权计算，最终得到目标点的插值值并存储在结果数组中。返回值`true`表示计算成功。

#### 辅助方法

```java
private double[] findSelectDataArr(double refObsID) {
    int length = m_dataArrOri.length - 1;
    double[] res = new double[length];
    for (int j = 0; j < m_dataArrOri[0].length; j++) {
        double obsID = m_dataArrOri[0][j];
        if (obsID == refObsID) {
            for (int i = 1; i < length + 1; i++) {
                res[i - 1] = m_dataArrOri[i][j];
            }
            break;
        }
    }
    return res;
}

private int findObsIdx(int[] disRankArr, int rank) {
    int idx = -99;
    for (int i = 0; i < disRankArr.length; i++) {
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
```

- **辅助方法**：包括查找特定观测站数据、根据秩找到观测站索引、根据数值获取插值数据类型、将插值结果写入文本文件等。

- 这段代码包含了四个方法，它们分别实现了插值计算过程中辅助功能。以下是对每个方法的详细解析。

  ### 1. `findSelectDataArr`

  ```
  private double[] findSelectDataArr(double refObsID) {
      int length = m_dataArrOri.length - 1;
      double[] res = new double[length];
      for (int j = 0; j < m_dataArrOri[0].length; j++) {
          double obsID = m_dataArrOri[0][j];
          if (obsID == refObsID) {
              for (int i = 1; i < length + 1; i++) {
                  res[i - 1] = m_dataArrOri[i][j];
              }
              break;
          }
      }
      return res;
  }
  ```

  这个方法的作用是根据给定的`refObsID`找到对应的观测数据数组。

  - `length`是数据数组的长度减一（因为通常第一行是表头）。
  - 初始化一个长度为`length`的数组`res`来存储结果。
  - 遍历原始数据数组的第一行，找到与`refObsID`匹配的观测点。
  - 将对应列中的观测数据复制到结果数组`res`中，并返回该数组。

  ### 2. `findObsIdx`

  ```
  private int findObsIdx(int[] disRankArr, int rank) {
      int idx = -99;
      for (int i = 0; i < disRankArr.length; i++) {
          if (disRankArr[i] == rank) {
              idx = i;
              break;
          }
      }
      return idx;
  }
  ```

  这个方法的作用是根据距离排名数组`disRankArr`和给定的排名`rank`找到相应的索引。

  - 初始化索引`idx`为-99（表示未找到）。
  - 遍历距离排名数组`disRankArr`，找到与给定排名`rank`匹配的索引，并返回该索引。

  ### 3. `getInterpDataTypeFromVal`

  ```
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
  ```

  这个方法的作用是根据整数值`val`返回相应的插值数据类型`InterpolationDataType`。

  - 初始化结果`res`为`null`。
  - 根据`val`的值，返回对应的插值数据类型。如果`val`是1，返回`Precipitation`；如果是2，返回`PET`；如果是3，返回`TMean`；如果是4，返回`Runoff`。

  ### 4. `writeDataArrNewToTxt`

  ```
  public void writeDataArrNewToTxt(String fileName) throws IOException {
      String Title = "";
      IOTxtFile file = new IOTxtFile();
      file.writeArrToTXT(fileName, Title, this.m_dataArrNew, new DecimalFormat("#0.00"));
  }
  ```

  这个方法的作用是将计算得到的新数据数组`m_dataArrNew`写入到指定的文本文件中。

  - 方法参数`fileName`是输出文件的名称。
  - 初始化标题`Title`为空字符串。
  - 创建一个`IOTxtFile`对象`file`。
  - 使用`file`对象的`writeArrToTXT`方法将数据数组`m_dataArrNew`写入到文本文件中，数据格式使用`DecimalFormat("#0.00")`表示小数点后两位。

  ### 总结

  这四个方法分别实现了插值计算过程中数据选择、索引查找、数据类型转换和结果输出的辅助功能。它们协同工作，保证了插值计算的顺利进行。

### 总结

这段代码通过距离反比加权插值法，将观测站的气象数据进行插值计算，生成指定目标站点的气象数据网格。代码包括数据初始化、距离计算、插值计算和结果输出等步骤。

### 参考站数量：

参考站数量（`m_refStaNum`）在距离反比加权插值法（IDW）中起着关键作用。具体来说，它决定了在计算目标点的插值值时，要考虑的最接近的观测站点的数量。

### 作用和原理

1. **选择最近的参考站**：
   在进行插值计算时，对于每一个目标点，需要从所有观测站点中选择距离最近的若干个站点（数量由`m_refStaNum`决定）。这些站点被称为参考站。
2. **计算距离**：
   计算目标点与这些参考站点之间的距离。距离越近，参考站点的权重越大。
3. **加权平均**：
   使用这些参考站点的观测数据和它们到目标点的距离进行加权平均计算。具体来说，距离的倒数平方（或其他形式的权重）作为权重，观测数据作为权值。
4. **插值计算**：
   根据加权平均的结果，计算出目标点的插值值。

### 示例

假设有以下观测站数据：

- 站点A：观测值 = 10，坐标 = (1, 1)
- 站点B：观测值 = 20，坐标 = (2, 2)
- 站点C：观测值 = 30，坐标 = (3, 3)
- 站点D：观测值 = 40，坐标 = (4, 4)

目标点的坐标为(2.5, 2.5)，`m_refStaNum`设置为2，这意味着在计算目标点的插值值时，将选择距离最近的两个参考站。

计算距离并选择最近的两个站点：

- 距离站点A：(2.5−1)2+(2.5−1)2=2.121(2.5−1)2+(2.5−1)2=2.121
- 距离站点B：(2.5−2)2+(2.5−2)2=0.707(2.5−2)2+(2.5−2)2=0.707
- 距离站点C：(2.5−3)2+(2.5−3)2=0.707(2.5−3)2+(2.5−3)2=0.707
- 距离站点D：(2.5−4)2+(2.5−4)2=2.121(2.5−4)2+(2.5−4)2=2.121

选择最近的两个站点B和C进行插值计算。

### 加权平均

使用距离的倒数平方作为权重：

- 站点B的权重：1/0.7072=21/0.7072=2
- 站点C的权重：1/0.7072=21/0.7072=2

插值值 = (20×2)+(30×2)2+2=252+2(20×2)+(30×2)=25

### 代码实现中的体现

在代码中，这一过程体现在以下几个部分：

1. **计算距离**：

   ```
   for (int j = 0; j < obsIDNum; j++) {
       double XObs = Double.valueOf(m_ObsIDArr[j][1]);
       double YObs = Double.valueOf(m_ObsIDArr[j][2]);
       distanceArr[j] = Math.sqrt(Math.pow(XObs - XTarget, 2) + Math.pow(YObs - YTarget, 2));
   }
   ```

2. **选择最近的参考站**：

   ```
   int[] disRankArr = SPTAAlg.calcRankSer(distanceArr);
   double[][] arrForInterp = new double[rowNum + 1][m_refStaNum];
   for (int j = 0; j < m_refStaNum; j++) {
       int rank = j + 1;
       int selectObsIdx = this.findObsIdx(disRankArr, rank);
   }
   ```

3. **加权平均计算**：

   ```
   double sum1 = 0, sum2 = 0;
   for (int j = 0; j < validDataSize; j++) {
       double temp1 = Math.pow(validDistanceVec.get(j), -2.0);
       sum2 += temp1;
       sum1 += validValVec.get(j) * temp1;
   }
   m_dataArrNew[k][i] = sum1 / sum2;
   ```

通过这些步骤，实现了基于参考站数量的距离反比加权插值计算，从而得到目标点的插值结果。
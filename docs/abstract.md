# Abstract

## Real-Time Air Quality Prediction System using GA-KELM

Air pollution has emerged as one of the most critical environmental challenges of the 21st century, directly impacting public health, especially in rapidly urbanizing regions. Accurate and timely prediction of Air Quality Index (AQI) is essential for enabling proactive measures to protect vulnerable populations and inform policy decisions. This paper presents a **Real-Time Air Quality Prediction System** powered by **GA-KELM** (Genetic Algorithm - Kernel Extreme Learning Machine), a novel hybrid machine learning approach that combines the computational efficiency of Kernel Extreme Learning Machines with the global optimization capabilities of Genetic Algorithms.

Unlike conventional machine learning models such as Support Vector Machines (SVM) and Artificial Neural Networks (ANN), which often suffer from slow training times, local optima convergence, and manual hyperparameter tuning requirements, **GA-KELM** offers several advantages:

1. **Automatic Hyperparameter Optimization**: The Genetic Algorithm automatically discovers optimal values for the regularization parameter (C) and kernel coefficient (gamma), eliminating manual tuning.

2. **Fast Training**: KELM's closed-form solution enables significantly faster training compared to iterative gradient-based methods.

3. **Strong Generalization**: The combination of kernel mapping and evolutionary optimization produces models that generalize well to unseen data.

4. **Real-Time Capability**: The efficient prediction process enables integration into real-time monitoring systems.

The proposed system integrates real-time AQI data from the **OpenWeatherMap Air Pollution API**, stores historical readings in a cloud-based **PostgreSQL** database, and presents predictions through a modern **React** dashboard with live WebSocket updates. The backend is built using **FastAPI**, ensuring high-performance asynchronous data processing. Background schedulers continuously collect data and retrain the model to adapt to evolving air quality patterns.

Experimental evaluation demonstrates that GA-KELM achieves competitive prediction accuracy with significantly reduced computational overhead compared to traditional approaches. The system architecture is designed for **scalability** and **cloud deployment** using **Railway**, making it suitable for production environments.

**Keywords**: Air Quality Index, AQI Prediction, Machine Learning, Kernel Extreme Learning Machine, Genetic Algorithm, GA-KELM, Real-Time Monitoring, FastAPI, React, Cloud Deployment
